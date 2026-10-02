"""
Combine completed ratings with the key to score each model.

Usage (from backend/):
    python -m evaluation.score_ratings evaluation/results/<run id>

Reads ratings.csv (filled in by raters) and ratings_key.csv. Blank cells are skipped, and the
"reference" rows are the controls. Scores are over the sentences a model ranked in its top
candidates.
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

SCALES = {"fluency_1to5": "fluency (1-5)", "code_mix_natural_1to5": "code-mix naturalness (1-5)"}
FLAGS = {"meaning_ok": "meaning ok", "gender_ok": "gender ok"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def score(ratings: list[dict[str, str]], key: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    """
    Mean rating per model.

    Args:
        ratings: Rows of ratings.csv.
        key: Rows of ratings_key.csv.

    Returns:
        For each model, the mean of each scale, the share of 1s for each yes/no column, and
        "rated", the number of rated sentences. A column with no ratings is omitted.
    """
    by_row = {r["row_id"]: r for r in ratings}
    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    rated: dict[str, set[str]] = defaultdict(set)
    for entry in key:
        row = by_row.get(entry["row_id"])
        if row is None:
            continue
        for column in (*SCALES, *FLAGS):
            text = row.get(column, "").strip()
            if text and text.upper() != "NA":
                values[entry["model"]][column].append(float(text))
                rated[entry["model"]].add(entry["row_id"])
    out: dict[str, dict[str, float]] = {}
    for model, columns in values.items():
        out[model] = {"rated": float(len(rated[model]))}
        for column, numbers in columns.items():
            out[model][column] = mean(numbers)
    return out


def render(scores: dict[str, dict[str, float]]) -> str:
    columns = [*SCALES, *FLAGS]
    labels = {**SCALES, **FLAGS}
    header = "| model | rated | " + " | ".join(labels[c] for c in columns) + " |"
    lines = [header, "|---|---|" + "---|" * len(columns)]
    for model, s in sorted(scores.items()):
        cells = [f"{s[c]:.2f}" if c in s else "" for c in columns]
        lines.append(f"| {model} | {s['rated']:.0f} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    ratings = read_csv(args.run_dir / "ratings.csv")
    key = read_csv(args.run_dir / "ratings_key.csv")
    scores = score(ratings, key)
    if not scores:
        print("No ratings found.", file=sys.stderr)
        return 1
    print(render(scores))
    return 0


if __name__ == "__main__":
    sys.exit(main())
