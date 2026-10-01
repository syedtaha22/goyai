import pytest

from app.config import Settings
from app.fallback import ExampleBank
from app.llm.base import LLMError
from app.schemas import SuggestRequest
from app.suggest import Suggester
from app.textutil import URDU_FULL_STOP
from app.tiles import TileBank, UnknownTileError
from tests.fakes import FakeLLM

pytestmark = pytest.mark.anyio

SETTINGS = Settings(llm_budget=1.0)
WATER_TILES = ["person_i_me", "action_want", "food_water"]


def reply(*pairs: tuple[str, str]) -> dict:
    return {"candidates": [{"urdu": u, "english": e, "style": "urdu"} for u, e in pairs]}


GOOD = reply(
    ("مجھے پانی چاہیے" + URDU_FULL_STOP, "I want water."),
    ("مجھے اور پانی چاہیے" + URDU_FULL_STOP, "I want more water."),
    ("مجھے پیاس لگی ہے" + URDU_FULL_STOP, "I am thirsty."),
)


async def make(llm: FakeLLM, settings: Settings = SETTINGS, *, loaded: bool = True) -> Suggester:
    tiles = TileBank.load(settings.data_dir / "tiles.json")
    examples = ExampleBank.load(settings.data_dir / "examples.json")
    suggester = Suggester(llm, tiles, examples, settings)
    if loaded:
        await suggester.warm()
    return suggester


def request(**kw) -> SuggestRequest:
    return SuggestRequest(**{"tiles": WATER_TILES, **kw})


async def test_model_candidates_are_used():
    llm = FakeLLM(responses=[GOOD])
    resp = await (await make(llm)).suggest(request())
    assert resp.source == "llm"
    assert resp.model == "fake-model"
    english = [c.english for c in resp.candidates]
    assert english == ["I want water.", "I want more water.", "I am thirsty."]
    assert len(llm.calls) == 1


async def test_prompt_contains_tiles_and_few_shot_examples():
    llm = FakeLLM(responses=[GOOD])
    await (await make(llm)).suggest(request())
    messages = llm.calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user" and "water" in messages[-1]["content"]
    assert [m["role"] for m in messages].count("assistant") == 4


async def test_schema_sent_matches_n():
    llm = FakeLLM(responses=[GOOD])
    await (await make(llm)).suggest(request(n=2))
    assert llm.calls[0]["schema"]["properties"]["candidates"]["maxItems"] == 2


async def test_default_and_different_modes_use_their_temperatures():
    llm = FakeLLM(responses=[GOOD])
    suggester = await make(llm)
    await suggester.suggest(request())
    await suggester.suggest(request(mode="different"))
    temperatures = [c["temperature"] for c in llm.calls]
    assert temperatures == [SETTINGS.temperature, SETTINGS.temperature_different]


async def test_exclude_reaches_prompt_and_filters_output():
    shown = "مجھے پانی چاہیے" + URDU_FULL_STOP
    llm = FakeLLM(responses=[GOOD])
    resp = await (await make(llm)).suggest(request(exclude=[shown], mode="different"))
    assert shown in llm.calls[0]["messages"][-1]["content"]
    assert shown not in [c.urdu for c in resp.candidates]
    assert resp.source == "llm"


async def test_output_truncated_to_n():
    resp = await (await make(FakeLLM(responses=[GOOD]))).suggest(request(n=1))
    assert len(resp.candidates) == 1


async def test_gender_reaches_prompt():
    llm = FakeLLM(responses=[GOOD])
    await (await make(llm)).suggest(request(profile={"gender": "female"}))
    assert "feminine" in llm.calls[0]["messages"][0]["content"]


async def test_unusable_output_is_retried_once():
    llm = FakeLLM(responses=[{"candidates": []}, GOOD])
    resp = await (await make(llm)).suggest(request())
    assert resp.source == "llm" and len(llm.calls) == 2


async def test_model_error_is_retried_once():
    llm = FakeLLM(responses=[LLMError("bad json"), GOOD])
    resp = await (await make(llm)).suggest(request())
    assert resp.source == "llm" and len(llm.calls) == 2


async def test_falls_back_after_two_failed_attempts():
    llm = FakeLLM(responses=[LLMError("down")])
    resp = await (await make(llm)).suggest(request())
    assert resp.source == "fallback" and resp.model is None
    assert len(llm.calls) == 2
    assert resp.candidates[0].urdu == "مجھے پانی چاہیے" + URDU_FULL_STOP


async def test_falls_back_when_every_candidate_is_rejected():
    junk = reply(("مجھے پانی چاہیے (Note: extra)", "I want water."))
    resp = await (await make(FakeLLM(responses=[junk]))).suggest(request())
    assert resp.source == "fallback"


async def test_falls_back_when_model_is_too_slow():
    llm = FakeLLM(responses=[GOOD], delay=1.0)
    suggester = await make(llm, Settings(llm_budget=0.05))
    resp = await suggester.suggest(request())
    assert resp.source == "fallback"


async def test_not_loaded_model_is_not_called_and_warmup_starts():
    llm = FakeLLM(responses=[GOOD])
    suggester = await make(llm, loaded=False)
    resp = await suggester.suggest(request())
    assert resp.source == "fallback" and llm.calls == []
    await suggester.stop()


async def test_failed_warmup_keeps_fallback_and_is_retried_on_next_request():
    llm = FakeLLM(responses=[GOOD], warmup_fails=True)
    suggester = await make(llm)
    assert suggester.loaded is False
    assert (await suggester.suggest(request())).source == "fallback"
    llm._warmup_fails = False
    await suggester.warm()
    assert suggester.loaded is True
    assert (await suggester.suggest(request())).source == "llm"


async def test_unknown_tile_raises():
    with pytest.raises(UnknownTileError):
        await (await make(FakeLLM())).suggest(request(tiles=["bogus"]))
