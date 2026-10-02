"""
Summarize a results folder and prepare the blind rating sheet.

Usage (from backend/):
    python -m evaluation.report evaluation/results/<run id> [--sample N]

Writes summary.md and summary.json (automatic metrics), ratings.csv (a shuffled sheet for
native-speaker raters, with the model names hidden) and ratings_key.csv (which model produced
each row).
"""

import argparse
import csv
import json
import random
import sys
from pathlib import Path

from app.textutil import comparison_key
from evaluation.cases import DEFAULT_CASES, EvalCase, load_cases
from evaluation.metrics import TOP_K, CaseResult, summarize

CONTROL_MODEL = "reference"
SHEET_SEED = 0
RATING_COLUMNS = ["meaning_ok", "fluency_1to5", "gender_ok", "code_mix_natural_1to5", "notes"]

_COLUMNS = [
    ("n", "n", "{:.0f}"),
    ("usable", "usable", "{:.1%}"),
    ("exact_at_1", "exact@1", "{:.1%}"),
    ("exact_at_3", "exact@3", "{:.1%}"),
    ("code_mixed_offered", "code-mixed offered", "{:.1%}"),
    ("mean_candidates", "candidates", "{:.2f}"),
    ("latency_p50", "p50 ms", "{:.0f}"),
    ("latency_p95", "p95 ms", "{:.0f}"),
]


def load_results(run_dir: Path) -> dict[str, list[CaseResult]]:
    """
    Read every model's results from a run folder, keyed by model tag.
    """
    out = {}
    for path in sorted(run_dir.glob("*.jsonl")):
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        out[meta["model"]] = [
            CaseResult(
                case_id=r["case_id"],
                source=r["source"],
                candidates=[tuple(c) for c in r["candidates"]],
                latency_ms=r["latency_ms"],
            )
            for r in rows
        ]
    return out


def markdown_table(rows: dict[str, dict[str, float]]) -> str:
    """
    Render per-model summaries as a Markdown table.
    """
    header = "| model | " + " | ".join(label for _, label, _ in _COLUMNS) + " |"
    rule = "|---|" + "---|" * len(_COLUMNS)
    lines = [header, rule]
    for model, summary in rows.items():
        cells = [
            fmt.format(summary[key]) if key in summary else "" for key, _, fmt in _COLUMNS
        ]
        lines.append(f"| {model} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_summary(
    results: dict[str, list[CaseResult]], cases: list[EvalCase]
) -> dict[str, dict[str, dict[str, float]]]:
    """
    Metrics per split (all, urdu, code_mixed) and model.
    """
    by_id = {c.id: c for c in cases}
    summary: dict[str, dict[str, dict[str, float]]] = {"all": {}, "urdu": {}, "code_mixed": {}}
    for model, model_results in results.items():
        model_results = [r for r in model_results if r.case_id in by_id]
        summary["all"][model] = summarize(model_results, by_id)
        for split in ("urdu", "code_mixed"):
            subset = [r for r in model_results if by_id[r.case_id].split == split]
            summary[split][model] = summarize(subset, by_id)
    return summary


def rating_rows(
    results: dict[str, list[CaseResult]], cases: list[EvalCase]
) -> tuple[list[dict], list[dict]]:
    """
    Build the blind rating sheet and its key.

    Each distinct sentence for a case appears once, however many models produced it, with at
    most the top candidates of each model. One reference sentence per case is added as a control,
    so raters' scores on known-good sentences can be compared with the models' sentences.
    Rows are shuffled with a fixed seed.

    Returns:
        (sheet rows, key rows). Key rows list (row_id, model, rank) for every sentence source.
    """
    by_id = {c.id: c for c in cases}
    sentences: dict[tuple[str, str], list[tuple[str, int]]] = {}
    display: dict[tuple[str, str], str] = {}

    def add(case_id: str, urdu: str, model: str, rank: int) -> None:
        key = (case_id, comparison_key(urdu))
        sentences.setdefault(key, []).append((model, rank))
        display.setdefault(key, urdu)

    for model, model_results in results.items():
        for r in model_results:
            if r.case_id not in by_id:
                continue
            for rank, (urdu, _) in enumerate(r.candidates[:TOP_K], start=1):
                add(r.case_id, urdu, model, rank)
    for case in cases:
        add(case.id, case.references[0], CONTROL_MODEL, 0)

    keys = sorted(sentences)
    random.Random(SHEET_SEED).shuffle(keys)
    sheet, key_rows = [], []
    for index, key in enumerate(keys, start=1):
        case = by_id[key[0]]
        row_id = f"r{index:04d}"
        sheet.append(
            {
                "row_id": row_id,
                "case_id": case.id,
                "split": case.split,
                "speaker_gender": case.gender or "",
                "intended_meaning": case.english,
                "urdu": display[key],
                **dict.fromkeys(RATING_COLUMNS, ""),
            }
        )
        key_rows += [
            {"row_id": row_id, "model": model, "rank": rank} for model, rank in sentences[key]
        ]
    return sheet, key_rows


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def sample_cases(cases: list[EvalCase], size: int) -> list[EvalCase]:
    """
    Draw a sample of cases for rating, with each split represented in proportion.

    The draw is seeded, so the same sample comes back for the same cases and size.

    Args:
        cases: All cases.
        size: Total number of cases wanted. A value of at least len(cases) returns all of them.
    """
    if size >= len(cases):
        return list(cases)
    rng = random.Random(SHEET_SEED)
    chosen: list[EvalCase] = []
    for split in ("urdu", "code_mixed"):
        members = [c for c in cases if c.split == split]
        share = round(size * len(members) / len(cases))
        chosen += rng.sample(members, min(share, len(members)))
    return sorted(chosen, key=lambda c: c.id)


def write_report(
    run_dir: Path, cases: list[EvalCase] | None = None, rating_sample: int | None = None
) -> None:
    """
    Write summary.md, summary.json, ratings.csv and ratings_key.csv into a run folder.

    Args:
        run_dir: The run folder holding the per-model results.
        cases: The cases that were run. Defaults to the full case file.
        rating_sample: When set, the rating sheet covers a sample of this many cases. The
            summary always covers all cases.
    """
    cases = cases if cases is not None else load_cases()
    results = load_results(run_dir)
    summary = build_summary(results, cases)

    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    sections = [
        f"# Results: {run_dir.name}\n",
        "exact@k counts a reference sentence among the top k candidates, so it is a lower bound: "
        "correct sentences that are not listed as references do not count. Fallback responses "
        "count as misses.\n",
    ]
    titles = (("all", "All cases"), ("urdu", "Urdu cases"), ("code_mixed", "Code-mixed cases"))
    for split, title in titles:
        sections.append(f"## {title}\n\n{markdown_table(summary[split])}\n")
    (run_dir / "summary.md").write_text("\n".join(sections), encoding="utf-8")

    rated_cases = sample_cases(cases, rating_sample) if rating_sample else cases
    sheet, key_rows = rating_rows(results, rated_cases)
    sheet_columns = ["row_id", "case_id", "split", "speaker_gender", "intended_meaning", "urdu"]
    write_csv(run_dir / "ratings.csv", sheet, sheet_columns + RATING_COLUMNS)
    write_csv(run_dir / "ratings_key.csv", key_rows, ["row_id", "model", "rank"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument(
        "--sample", type=int, help="Put only a sample of this many cases in the rating sheet"
    )
    args = parser.parse_args(argv)
    write_report(args.run_dir, load_cases(args.cases), args.sample)
    print((args.run_dir / "summary.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
