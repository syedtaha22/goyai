import asyncio
import logging
import warnings
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sentencepiece as spm
import torch
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

from app.config import Settings
from app.decoder.generation import beam_search
from app.decoder.joint import JointTransformer, write_english
from app.decoder.modeling import Transformer
from app.engine import EngineError
from app.postprocess import clean_urdu
from app.schemas import Candidate, SuggestRequest
from app.textutil import comparison_key, count_letters
from app.tiles import Tile

logger = logging.getLogger("goyai")

SEP = "<sep>"
TILE_JOIN = " + "
WEIGHTS = "model.safetensors"
TOKENIZER = "tokenizer.model"
ENGLISH_TOKENIZER = "english_tokenizer.model"

# Beam width bounds. The width is one more than the number of sentences wanted and skipped.
MIN_BEAMS = 4
MAX_BEAMS = 12
# Decoded sentence lists kept for repeated tile selections.
CACHE_SIZE = 256
# Number of sentences, from the top, that get an English sentence.
ENGLISH_FOR = 4
# The id of the piece that closes the Urdu sentence is the third piece of the English vocabulary.
MARKER_PIECE = 2
MAX_ENGLISH = 30


class TransformerEngine:
    """
    CandidateEngine backed by a small decoder-only transformer that runs in this process.

    The model reads the Urdu labels of the selected tiles and writes the sentence. A model that
    also has English pieces (the weights contain `english_head.weight`) writes an English sentence
    after each of the first sentences, and the others carry none.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._repo = settings.decoder_repo
        self._device = self._pick_device(settings.decoder_device)
        self._model: Transformer | JointTransformer | None = None
        self._tokenizer: spm.SentencePieceProcessor | None = None
        self._english: spm.SentencePieceProcessor | None = None
        # All torch work runs on one thread, which also fixes the number of threads it uses.
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="decoder")
        self._cache: OrderedDict[tuple[tuple[str, ...], int], list[tuple[str, str | None]]] = (
            OrderedDict()
        )

    @staticmethod
    def _pick_device(name: str) -> torch.device:
        if name == "auto":
            name = "cuda" if torch.cuda.is_available() else "cpu"
        return torch.device(name)

    @property
    def model(self) -> str:
        return self._repo

    def _load(self) -> None:
        weights = Path(hf_hub_download(self._repo, WEIGHTS))
        tokenizer = Path(hf_hub_download(self._repo, TOKENIZER))

        if self._settings.decoder_threads and self._device.type == "cpu":
            torch.set_num_threads(self._settings.decoder_threads)

        state = load_file(weights)
        joint = "english_head.weight" in state
        model = (JointTransformer if joint else Transformer).from_state_dict(state)
        if self._settings.decoder_quantize and self._device.type == "cpu":
            model = self._quantized(model)
        self._model = model.to(self._device)
        self._tokenizer = spm.SentencePieceProcessor(model_file=str(tokenizer))

        if joint:
            english = Path(hf_hub_download(self._repo, ENGLISH_TOKENIZER))
            self._english = spm.SentencePieceProcessor(model_file=str(english))

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
        return self._model is not None

    async def aclose(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._model = None

    def _decode(self, labels: list[str], beams: int) -> list[tuple[str, str | None]]:
        key = (tuple(labels), beams)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        sentences = self._beam(labels, beams)
        self._cache[key] = sentences
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)

        return sentences

    def _beam(self, labels: list[str], beams: int) -> list[tuple[str, str | None]]:
        """
        The sentences of the beam search, best first, each with its English sentence or None.
        """
        assert self._model is not None and self._tokenizer is not None
        tok = self._tokenizer
        prompt = [tok.bos_id(), *tok.encode(TILE_JOIN.join(labels)), tok.piece_to_id(SEP)]

        s = self._settings
        room = self._model.max_len - len(prompt)
        if room < 2:
            raise EngineError("the tile selection is too long for the model")

        joint = isinstance(self._model, JointTransformer)
        first_english = self._model.urdu_vocab if joint else 0
        outputs = beam_search(
            self._model,
            prompt,
            first_english + MARKER_PIECE if joint else tok.eos_id(),
            beams=beams,
            max_new=min(s.decoder_max_new, room),
            length_alpha=s.decoder_length_alpha,
        )

        if not joint:
            return [(tok.decode(tokens), None) for tokens in outputs]

        sentences: list[str] = []
        for tokens in outputs:
            text = tok.decode([t for t in tokens if t < first_english])
            if text and text not in sentences:
                sentences.append(text)

        marker = first_english + MARKER_PIECE
        result: list[tuple[str, str | None]] = []
        for i, text in enumerate(sentences):
            english = None
            if i < ENGLISH_FOR:
                english_prompt = [*prompt, *tok.encode(text), marker]
                room = self._model.max_len - len(english_prompt)
                ids = (
                    write_english(self._model, english_prompt, tok.eos_id(), min(MAX_ENGLISH, room))
                    if room > 1
                    else []
                )
                english = self._english.decode([t - first_english for t in ids]).strip() or None
            result.append((text, english))

        return result

    async def candidates(self, selected: list[Tile], req: SuggestRequest) -> list[Candidate]:
        beams = min(MAX_BEAMS, max(MIN_BEAMS, req.n + 1 + len(req.exclude)))
        labels = [tile.urdu for tile in selected]

        loop = asyncio.get_running_loop()
        sentences = await loop.run_in_executor(self._executor, self._decode, labels, beams)

        seen = {comparison_key(s) for s in req.exclude}
        out: list[Candidate] = []

        for sentence, english in sentences:
            urdu = clean_urdu(sentence)
            if urdu is None or comparison_key(urdu) in seen:
                continue

            seen.add(comparison_key(urdu))
            style = "code_mixed" if count_letters(urdu)[1] > 0 else "urdu"
            out.append(Candidate(urdu=urdu, english=english, style=style))

            if len(out) == req.n:
                break

        return out
