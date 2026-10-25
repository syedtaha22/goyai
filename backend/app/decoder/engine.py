import asyncio
import logging
import warnings
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sentencepiece as spm
import torch

from app.config import Settings
from app.decoder.beam import beam_search
from app.decoder.model import Transformer
from app.engine import EngineError
from app.postprocess import clean_urdu
from app.schemas import Candidate, SuggestRequest
from app.textutil import comparison_key, count_letters
from app.tiles import Tile

logger = logging.getLogger("goyai")

SEP = "<sep>"
TILE_JOIN = " + "
WEIGHTS = "transformer.pt"
TOKENIZER = "urdu_bpe.model"

# Beam width bounds. The width is one more than the number of sentences wanted and skipped.
MIN_BEAMS = 4
MAX_BEAMS = 12
# Decoded sentence lists kept for repeated tile selections.
CACHE_SIZE = 256


class TransformerEngine:
    """
    CandidateEngine backed by a small decoder-only transformer that runs in this process.

    The model reads the Urdu labels of the selected tiles and writes the sentence. It produces no
    English translation, so its candidates carry none.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._dir: Path = settings.decoder_dir
        self._device = self._pick_device(settings.decoder_device)
        self._model: Transformer | None = None
        self._tokenizer: spm.SentencePieceProcessor | None = None
        # All torch work runs on one thread, which also fixes the number of threads it uses.
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="decoder")
        self._cache: OrderedDict[tuple[tuple[str, ...], int], list[str]] = OrderedDict()

    @staticmethod
    def _pick_device(name: str) -> torch.device:
        if name == "auto":
            name = "cuda" if torch.cuda.is_available() else "cpu"
        return torch.device(name)

    @property
    def model(self) -> str:
        return f"transformer-{self._device.type}"

    def _load(self) -> None:
        weights, tokenizer = self._dir / WEIGHTS, self._dir / TOKENIZER
        if not weights.exists() or not tokenizer.exists():
            raise EngineError(f"decoder files not found in {self._dir}")

        if self._settings.decoder_threads and self._device.type == "cpu":
            torch.set_num_threads(self._settings.decoder_threads)

        state = torch.load(weights, map_location="cpu", weights_only=True)
        model = Transformer.from_state_dict(state)
        if self._settings.decoder_quantize and self._device.type == "cpu":
            model = self._quantized(model)
        self._model = model.to(self._device)
        self._tokenizer = spm.SentencePieceProcessor(model_file=str(tokenizer))

        # One decode compiles the kernels so the first request is as fast as the others.
        self._beam(["x"], MIN_BEAMS)

    @staticmethod
    def _quantized(model: Transformer) -> Transformer:
        """
        The model with 8-bit linear layers, or the model itself when torch cannot quantize it.
        """
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return torch.ao.quantization.quantize_dynamic(model, {torch.nn.Linear}, torch.qint8)
        except Exception as exc:
            logger.warning("Quantization is unavailable, the decoder runs in float32: %r", exc)
            return model

    async def warmup(self) -> None:
        if self._model is not None:
            return
        try:
            await asyncio.get_running_loop().run_in_executor(self._executor, self._load)
        except EngineError:
            raise
        except Exception as exc:
            raise EngineError(f"decoder failed to load: {exc!r}") from exc

    async def is_ready(self) -> bool:
        return (self._dir / WEIGHTS).exists() and (self._dir / TOKENIZER).exists()

    async def aclose(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._model = None

    def _decode(self, labels: list[str], beams: int) -> list[str]:
        key = (tuple(labels), beams)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        sentences = self._beam(labels, beams)
        self._cache[key] = sentences
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)

        return sentences

    def _beam(self, labels: list[str], beams: int) -> list[str]:
        assert self._model is not None and self._tokenizer is not None
        tok = self._tokenizer
        prompt = [tok.bos_id(), *tok.encode(TILE_JOIN.join(labels)), tok.piece_to_id(SEP)]

        s = self._settings
        room = self._model.max_len - len(prompt)
        if room < 2:
            raise EngineError("the tile selection is too long for the model")

        outputs = beam_search(
            self._model,
            prompt,
            tok.eos_id(),
            beams=beams,
            max_new=min(s.decoder_max_new, room),
            length_alpha=s.decoder_length_alpha,
        )

        return [tok.decode(tokens) for tokens in outputs]

    async def candidates(self, selected: list[Tile], req: SuggestRequest) -> list[Candidate]:
        beams = min(MAX_BEAMS, max(MIN_BEAMS, req.n + 1 + len(req.exclude)))
        labels = [tile.urdu for tile in selected]

        loop = asyncio.get_running_loop()
        sentences = await loop.run_in_executor(self._executor, self._decode, labels, beams)

        seen = {comparison_key(s) for s in req.exclude}
        out: list[Candidate] = []

        for sentence in sentences:
            urdu = clean_urdu(sentence)
            if urdu is None or comparison_key(urdu) in seen:
                continue

            seen.add(comparison_key(urdu))
            style = "code_mixed" if count_letters(urdu)[1] > 0 else "urdu"
            out.append(Candidate(urdu=urdu, english=None, style=style))

            if len(out) == req.n:
                break

        return out
