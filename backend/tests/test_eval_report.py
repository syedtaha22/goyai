import csv
import json

import pytest

from app.config import Settings
from app.textutil import URDU_FULL_STOP
from evaluation import report, run, score_ratings
from evaluation.cases import EvalCase
from evaluation.metrics import CaseResult
from tests.fakes import FakeLLM

pytestmark = pytest.mark.anyio

WATER = "مجھے پانی چاہیے"
HOME = "مجھے گھر جانا ہے"
MILK = "مجھے دودھ چاہیے"


def make_case(case_id: str, ref: str, tiles: list[str], split: str = "urdu") -> EvalCase:
    return EvalCase(id=case_id, split=split, tiles=tiles, references=[ref], english="meaning")


CASES = [
    make_case("u001", WATER, ["person_i_me", "action_want", "food_water"]),
    make_case("c001", "مجھے school جانا ہے", ["person_i_me", "place_school"], "code_mixed"),
]


def reply(*sentences: str) -> dict:
    items = [{"urdu": s, "english": f"E{i}.", "style": "urdu"} for i, s in enumerate(sentences)]
    return {"candidates": items}


def test_rating_sheet_dedupes_across_models_and_adds_controls():
    results = {
        "m1": [CaseResult("u001", "llm", [(WATER, "urdu"), (HOME, "urdu")], 10)],
        "m2": [CaseResult("u001", "llm", [(WATER, "urdu"), (MILK, "urdu")], 10)],
    }
    sheet, key = report.rating_rows(results, CASES[:1])
    urdu = [r["urdu"] for r in sheet]
    assert sorted(urdu) == sorted([WATER, HOME, MILK])
    assert len(set(urdu)) == len(urdu)
    water_id = next(r["row_id"] for r in sheet if r["urdu"] == WATER)
    sources = {(k["model"], k["rank"]) for k in key if k["row_id"] == water_id}
    assert sources == {("m1", 1), ("m2", 1), ("reference", 0)}


def test_rating_sheet_hides_models_and_is_deterministic():
    results = {"m1": [CaseResult("u001", "llm", [(HOME, "urdu")], 10)]}
    sheet1, _ = report.rating_rows(results, CASES)
    sheet2, _ = report.rating_rows(results, CASES)
    assert sheet1 == sheet2
    assert "model" not in sheet1[0] and "m1" not in json.dumps(sheet1, ensure_ascii=False)
    assert {r["case_id"] for r in sheet1} == {"u001", "c001"}


def test_rating_sheet_skips_fallback_and_limits_to_top_candidates():
    five = [(f"مجھے {w} چاہیے", "urdu") for w in ["الف", "ب", "پ", "ت", "ٹ"]]
    results = {
        "m1": [CaseResult("u001", "fallback", [], 5)],
        "m2": [CaseResult("u001", "llm", five, 5)],
    }
    sheet, key = report.rating_rows(results, CASES[:1])
    models = {k["model"] for k in key}
    assert models == {"m2", "reference"}
    assert sum(k["model"] == "m2" for k in key) == 3


async def test_run_model_records_model_candidates_and_fallbacks():
    good = reply(WATER + URDU_FULL_STOP, HOME + URDU_FULL_STOP)
    llm = FakeLLM(responses=[good, good, {}])
    settings = Settings(llm_budget=5.0)
    results = await run.run_model(settings, CASES, client=llm)
    assert [r.source for r in results] == ["llm", "fallback"]
    assert [u for u, _ in results[0].candidates][0].startswith(WATER)
    assert results[1].candidates == []
    # The untimed first request, one request for the first case, two attempts for the second.
    assert len(llm.calls) == 4


async def test_run_model_fails_when_model_cannot_load():
    with pytest.raises(RuntimeError):
        await run.run_model(Settings(), CASES, client=FakeLLM(warmup_fails=True))


async def test_run_model_passes_speaker_gender():
    llm = FakeLLM(responses=[reply(WATER)])
    gendered = EvalCase(
        id="u900",
        split="urdu",
        tiles=["person_i_me"],
        references=["x"],
        english="x",
        gender="female",
    )
    await run.run_model(Settings(), [gendered], client=llm)
    assert "feminine" not in llm.calls[0]["messages"][0]["content"]  # the untimed first request
    assert "feminine" in llm.calls[-1]["messages"][0]["content"]


async def test_full_report_round_trip(tmp_path):
    settings = Settings(model="m1", seed=0)
    llm = FakeLLM(responses=[reply(WATER), reply(WATER), reply("مجھے hospital جانا ہے")])
    results = await run.run_model(settings, CASES, client=llm)
    run.write_run(tmp_path, settings, report.DEFAULT_CASES, results, "9.9.9")
    report.write_report(tmp_path, CASES)

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["all"]["m1"]["exact_at_1"] == 0.5
    assert summary["urdu"]["m1"]["n"] == 1 and summary["code_mixed"]["m1"]["n"] == 1
    assert summary["code_mixed"]["m1"]["code_mixed_offered"] == 1.0
    assert "| m1 |" in (tmp_path / "summary.md").read_text(encoding="utf-8")

    meta = json.loads((tmp_path / "m1.meta.json").read_text(encoding="utf-8"))
    assert meta["model"] == "m1" and meta["seed"] == 0 and meta["ollama_version"] == "9.9.9"
    assert len(meta["cases_sha256"]) == 64 and len(meta["prompts_sha256"]) == 64

    rows = list(csv.DictReader((tmp_path / "ratings.csv").open(encoding="utf-8-sig")))
    assert {"row_id", "urdu", "meaning_ok", "fluency_1to5"} <= set(rows[0])
    assert "model" not in rows[0]
    # u001: the model's sentence equals the reference, so one row. c001: model row and control.
    assert len(rows) == 3


def test_sample_cases_is_stratified_seeded_and_bounded():
    from evaluation.cases import load_cases

    cases = load_cases()
    sample = report.sample_cases(cases, 40)
    assert 38 <= len(sample) <= 42
    assert sample == report.sample_cases(cases, 40)
    splits = {c.split for c in sample}
    assert splits == {"urdu", "code_mixed"}
    assert len(report.sample_cases(cases, 10_000)) == len(cases)


def test_report_with_sample_limits_the_rating_sheet(tmp_path):
    results = {"m1": [CaseResult(c.id, "llm", [(WATER, "urdu")], 5) for c in CASES]}
    sheet_all, _ = report.rating_rows(results, CASES)
    sheet_one, _ = report.rating_rows(results, CASES[:1])
    assert len(sheet_one) < len(sheet_all)


def write_ratings(tmp_path, rows: list[dict]) -> None:
    path = tmp_path / "ratings.csv"
    columns = ["row_id", "meaning_ok", "fluency_1to5", "gender_ok", "code_mix_natural_1to5"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows([{c: r.get(c, "") for c in columns} for r in rows])


def test_score_ratings_means_ignore_blanks_and_na(tmp_path):
    write_ratings(
        tmp_path,
        [
            {"row_id": "r1", "meaning_ok": "1", "fluency_1to5": "5", "gender_ok": "NA"},
            {"row_id": "r2", "meaning_ok": "0", "fluency_1to5": "3", "gender_ok": "1"},
            {"row_id": "r3", "meaning_ok": "", "fluency_1to5": ""},
        ],
    )
    key = [
        {"row_id": "r1", "model": "m1", "rank": "1"},
        {"row_id": "r2", "model": "m1", "rank": "2"},
        {"row_id": "r3", "model": "m1", "rank": "3"},
        {"row_id": "r1", "model": "reference", "rank": "0"},
    ]
    scores = score_ratings.score(score_ratings.read_csv(tmp_path / "ratings.csv"), key)
    assert scores["m1"]["fluency_1to5"] == 4.0
    assert scores["m1"]["meaning_ok"] == 0.5
    assert scores["m1"]["gender_ok"] == 1.0
    assert scores["m1"]["rated"] == 2.0
    assert scores["reference"]["fluency_1to5"] == 5.0
    assert "code_mix_natural_1to5" not in scores["m1"]
    assert "| m1 | 2 |" in score_ratings.render(scores)
