import math
from dataclasses import dataclass
from statistics import median

from app.textutil import comparison_key
from evaluation.cases import EvalCase

TOP_K = 3


@dataclass(frozen=True)
class CaseResult:
    """
    The outcome of one request for one case.

    Attributes:
        case_id: The EvalCase id.
        source: "llm" or "fallback" (fallback means the model gave nothing usable).
        candidates: (urdu, style) pairs in rank order. Empty when source is "fallback".
        latency_ms: Time taken for the request.
    """

    case_id: str
    source: str
    candidates: list[tuple[str, str]]
    latency_ms: int


def hit_rank(candidates: list[str], references: list[str]) -> int | None:
    """
    Rank (1-based) of the first candidate that matches a reference, or None.

    A candidate matches when it equals a reference ignoring case, spacing and punctuation.
    This is a strict lower bound on quality, because a correct sentence that is not listed
    as a reference does not match.

    Args:
        candidates: Candidate sentences in rank order.
        references: Acceptable sentences.
    """
    reference_keys = {comparison_key(ref) for ref in references}
    for rank, candidate in enumerate(candidates, start=1):
        if comparison_key(candidate) in reference_keys:
            return rank
    return None


def percentile(values: list[int], q: float) -> float:
    """
    The q-th percentile (0 to 100) of a list, by nearest rank. Returns nan for an empty list.
    """
    if not values:
        return math.nan
    ordered = sorted(values)
    index = max(0, math.ceil(q / 100 * len(ordered)) - 1)
    return float(ordered[index])


def summarize(results: list[CaseResult], cases: dict[str, EvalCase]) -> dict[str, float]:
    """
    Aggregate metrics over results.

    Fallback responses count as misses, because they do not come from the model. Rates are
    fractions of all results.

    Args:
        results: One result per case.
        cases: The cases, keyed by id.

    Returns:
        A dict with n, usable, exact_at_1, exact_at_3, code_mixed_offered, mean_candidates,
        latency_p50 and latency_p95.
    """
    n = len(results)
    if n == 0:
        return {"n": 0}
    usable = [r for r in results if r.source == "llm" and r.candidates]

    def rate(count: int) -> float:
        return count / n

    def hits(k: int) -> int:
        count = 0
        for r in usable:
            rank = hit_rank([u for u, _ in r.candidates], cases[r.case_id].references)
            count += rank is not None and rank <= k
        return count

    return {
        "n": n,
        "usable": rate(len(usable)),
        "exact_at_1": rate(hits(1)),
        "exact_at_3": rate(hits(TOP_K)),
        "code_mixed_offered": rate(
            sum(any(style == "code_mixed" for _, style in r.candidates) for r in usable)
        ),
        "mean_candidates": sum(len(r.candidates) for r in usable) / len(usable) if usable else 0.0,
        "latency_p50": median(r.latency_ms for r in results),
        "latency_p95": percentile([r.latency_ms for r in results], 95),
    }
