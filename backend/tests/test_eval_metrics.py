import math

from app.textutil import URDU_FULL_STOP
from evaluation.cases import EvalCase
from evaluation.metrics import CaseResult, hit_rank, percentile, summarize

WATER = "مجھے پانی چاہیے"
HOME = "مجھے گھر جانا ہے"
MILK = "مجھے دودھ چاہیے"


def case(case_id: str, refs: list[str], split: str = "urdu") -> EvalCase:
    return EvalCase(id=case_id, split=split, tiles=["person_i_me"], references=refs, english="x")


def result(case_id: str, candidates: list[tuple[str, str]], source="llm", latency=100):
    return CaseResult(case_id=case_id, source=source, candidates=candidates, latency_ms=latency)


def test_hit_rank_ignores_case_spacing_and_punctuation():
    assert hit_rank(["Please  WAIT."], ["please wait"]) == 1
    assert hit_rank([WATER + URDU_FULL_STOP], [WATER]) == 1


def test_hit_rank_returns_first_matching_rank_and_requires_exact_words():
    assert hit_rank([HOME, MILK, WATER], [WATER]) == 3
    assert hit_rank([HOME, MILK], ["x"]) is None
    # A sentence about a different item or person is not a hit.
    assert hit_rank([MILK], [WATER]) is None
    assert hit_rank(["مجھے ابو سے محبت ہے"], ["مجھے امی سے محبت ہے"]) is None


def test_hit_rank_uses_any_reference():
    assert hit_rank([HOME], [WATER, HOME]) == 1


def test_percentile_nearest_rank():
    values = list(range(1, 101))
    assert percentile(values, 50) == 50
    assert percentile(values, 95) == 95
    assert percentile([7], 95) == 7
    assert math.isnan(percentile([], 95))


def test_summarize_counts_hits_and_ranks():
    cases = {c.id: c for c in [case("a", [WATER]), case("b", [HOME]), case("c", [MILK])]}
    results = [
        result("a", [(WATER, "urdu"), (HOME, "urdu")], latency=100),
        result("b", [(MILK, "urdu"), (HOME, "urdu")], latency=200),
        result("c", [(WATER, "urdu"), (HOME, "urdu"), (MILK, "urdu")], latency=300),
    ]
    s = summarize(results, cases)
    assert s["n"] == 3 and s["usable"] == 1.0
    assert s["exact_at_1"] == 1 / 3
    assert s["exact_at_3"] == 1.0
    assert s["mean_candidates"] == 7 / 3
    assert s["latency_p50"] == 200 and s["latency_p95"] == 300


def test_fallback_and_empty_results_count_as_misses():
    cases = {"a": case("a", [WATER]), "b": case("b", [WATER])}
    results = [result("a", [(WATER, "urdu")], source="fallback"), result("b", [])]
    s = summarize(results, cases)
    assert s["usable"] == 0.0 and s["exact_at_3"] == 0.0 and s["mean_candidates"] == 0.0


def test_code_mixed_offered_rate():
    cases = {"a": case("a", ["x"], "code_mixed"), "b": case("b", ["y"], "code_mixed")}
    results = [
        result("a", [("مجھے school جانا ہے", "code_mixed")]),
        result("b", [("مجھے اسکول جانا ہے", "urdu")]),
    ]
    assert summarize(results, cases)["code_mixed_offered"] == 0.5


def test_summarize_empty():
    assert summarize([], {}) == {"n": 0}
