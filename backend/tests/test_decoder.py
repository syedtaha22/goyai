import pytest
import sentencepiece as spm
import torch
from safetensors.torch import save_file

from app.config import Settings
from app.decoder import engine as decoder_engine
from app.decoder.engine import TOKENIZER, WEIGHTS, TransformerEngine
from app.decoder.generation import beam_search
from app.decoder.modeling import Transformer
from app.engine import EngineError
from app.schemas import SuggestRequest
from app.tiles import Tile

pytestmark = pytest.mark.anyio

CORPUS = ["مجھے پانی چاہیے", "میں گھر جانا چاہتا ہوں", "مجھے بھوک لگی ہے", "پانی + چاہیے"] * 10


def tiny_model() -> Transformer:
    torch.manual_seed(0)
    return Transformer(vocab_size=40, d_model=64, n_layers=2, max_len=64).eval()


def test_cached_decoding_matches_a_full_pass():
    model = tiny_model()
    tokens = torch.randint(0, 40, (3, 9))

    with torch.inference_mode():
        full, _ = model(tokens)
        logits, cache = model(tokens[:, :4])
        for i in range(4, 9):
            logits, cache = model(tokens[:, i : i + 1], cache)

    assert torch.allclose(full, logits, atol=1e-5)


def test_state_dict_round_trip_rebuilds_the_same_shape():
    model = tiny_model()
    rebuilt = Transformer.from_state_dict(model.state_dict())

    assert rebuilt.max_len == 64
    assert len(rebuilt.blocks) == 2
    assert rebuilt.embed.weight.shape == (40, 64)


def test_beam_search_returns_ranked_sequences_without_the_end_token():
    model = tiny_model()
    kwargs = {"beams": 4, "max_new": 12, "length_alpha": 0.7}

    first = beam_search(model, [1, 5, 6], eos=2, **kwargs)
    second = beam_search(model, [1, 5, 6], eos=2, **kwargs)

    assert first == second
    assert 0 < len(first) <= 8
    assert all(2 not in tokens and len(tokens) <= 12 for tokens in first)


def make_files(folder):
    """
    Write a tokenizer and the weights of a small model to the folder, as the repository holds them.
    """
    folder.mkdir(parents=True, exist_ok=True)
    corpus = folder / "corpus.txt"
    corpus.write_text("\n".join(CORPUS), encoding="utf-8")
    spm.SentencePieceTrainer.train(
        input=str(corpus),
        model_prefix=str(folder / TOKENIZER.removesuffix(".model")),
        vocab_size=40,
        model_type="bpe",
        user_defined_symbols=["<sep>"],
        bos_id=1,
        eos_id=2,
        unk_id=0,
        character_coverage=1.0,
    )
    model = Transformer(vocab_size=40, d_model=64, n_layers=2, max_len=64)
    save_file(model.state_dict(), folder / WEIGHTS)


def serve_from(monkeypatch, folder, requested=None):
    """
    Make the engine take the files made by make_files from the folder instead of downloading them.
    """
    make_files(folder)

    def download(repo, name):
        if requested is not None:
            requested.append((repo, name))
        return str(folder / name)

    monkeypatch.setattr(decoder_engine, "hf_hub_download", download)


def tile(urdu: str) -> Tile:
    return Tile(tile_id="t", category="c", english="x", urdu=urdu)


@pytest.fixture
def engine(tmp_path, monkeypatch):
    serve_from(monkeypatch, tmp_path)
    return TransformerEngine(Settings(decoder_repo="owner/name", decoder_device="cpu"))


async def test_engine_is_named_after_its_repository(engine):
    assert engine.model == "owner/name"


async def test_engine_loads_and_answers(engine):
    assert not await engine.is_ready()
    await engine.warmup()
    assert await engine.is_ready()

    out = await engine.candidates([tile("پانی"), tile("چاہیے")], SuggestRequest(tiles=["a"]))

    assert len(out) <= 3
    assert all(c.english is None and c.urdu.endswith(("۔", "؟")) for c in out)


async def test_engine_repeats_a_request_from_its_cache(engine):
    await engine.warmup()
    selected = [tile("پانی")]
    req = SuggestRequest(tiles=["a"])

    first = await engine.candidates(selected, req)
    second = await engine.candidates(selected, req)

    assert first == second
    assert len(engine._cache) == 1


async def test_engine_skips_excluded_sentences(engine):
    await engine.warmup()
    selected = [tile("پانی")]
    first = await engine.candidates(selected, SuggestRequest(tiles=["a"]))

    again = await engine.candidates(
        selected, SuggestRequest(tiles=["a"], exclude=[c.urdu for c in first])
    )

    assert {c.urdu for c in first}.isdisjoint(c.urdu for c in again)


async def test_engine_downloads_the_files_from_the_hub(tmp_path, monkeypatch):
    requested = []
    serve_from(monkeypatch, tmp_path, requested)
    engine = TransformerEngine(Settings(decoder_repo="owner/name", decoder_device="cpu"))

    await engine.warmup()

    assert requested == [("owner/name", WEIGHTS), ("owner/name", TOKENIZER)]


async def test_a_failed_download_is_reported(monkeypatch):
    def download(repo, name):
        raise OSError("offline")

    monkeypatch.setattr(decoder_engine, "hf_hub_download", download)
    engine = TransformerEngine(Settings(decoder_repo="owner/name", decoder_device="cpu"))

    assert not await engine.is_ready()
    with pytest.raises(EngineError):
        await engine.warmup()


async def test_overlong_selection_is_rejected(engine):
    await engine.warmup()
    long_label = "پانی " * 80

    with pytest.raises(EngineError):
        await engine.candidates([tile(long_label)], SuggestRequest(tiles=["a"]))
