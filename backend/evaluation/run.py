"""
Run the suggestion pipeline on the evaluation cases for one or more models.

Usage (from backend/):
    python -m evaluation.run --models qwen3.5:4b gemma3:4b

Results are written to evaluation/results/<run id>/, then summarized by evaluation.report.
"""

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.config import Settings
from app.fallback import ExampleBank
from app.llm.base import LLMClient
from app.llm.ollama import OllamaClient
from app.prompt import FEW_SHOT_COUNT
from app.schemas import Profile, SuggestRequest
from app.suggest import Suggester
from app.tiles import TileBank
from evaluation import report
from evaluation.cases import DEFAULT_CASES, EvalCase, cases_digest, load_cases
from evaluation.metrics import CaseResult

RESULTS_DIR = Path(__file__).resolve().parent / "results"
CANDIDATES_PER_CASE = 3
# Selection for the untimed first request. It should not repeat any case, so no case benefits
# from caching.
WARMUP_TILES = ["person_i_me", "feeling_okay", "social_yes"]


def safe_name(model: str) -> str:
    """
    File-name form of a model tag.
    """
    return model.replace(":", "_").replace("/", "_")


async def run_model(
    settings: Settings, cases: list[EvalCase], client: LLMClient | None = None
) -> list[CaseResult]:
    """
    Run every case through the suggestion pipeline with one model.

    A response that falls back to the curated examples is recorded with no candidates, because
    those sentences do not come from the model. One untimed request on a selection that is not
    a case runs first, so one-off initialization after loading does not count towards the
    latencies.

    Args:
        settings: Settings naming the model and its sampling options.
        cases: The cases to run, in order.
        client: Model client. Defaults to an OllamaClient built from the settings.

    Raises:
        RuntimeError: If the model cannot be loaded.
    """
    client = client or OllamaClient(settings)
    tiles = TileBank.load(settings.data_dir / "tiles.json")
    examples = ExampleBank.load(settings.data_dir / "examples.json")
    suggester = Suggester(client, tiles, examples, settings)
    try:
        await suggester.warm()
        if not suggester.loaded:
            raise RuntimeError(f"model {settings.model} could not be loaded")

        def request_for(case: EvalCase) -> SuggestRequest:
            return SuggestRequest(
                tiles=case.tiles, profile=Profile(gender=case.gender), n=CANDIDATES_PER_CASE
            )

        await suggester.suggest(SuggestRequest(tiles=WARMUP_TILES, n=CANDIDATES_PER_CASE))
        results = []
        for case in cases:
            response = await suggester.suggest(request_for(case))
            from_model = response.source == "llm"
            results.append(
                CaseResult(
                    case_id=case.id,
                    source=response.source,
                    candidates=[(c.urdu, c.style) for c in response.candidates]
                    if from_model
                    else [],
                    latency_ms=response.latency_ms,
                )
            )
        return results
    finally:
        await client.aclose()


async def unload(settings: Settings) -> None:
    """
    Ask Ollama to release the model's memory so the next model has the whole GPU.
    """
    async with httpx.AsyncClient(base_url=settings.ollama_url, timeout=30) as http:
        await http.post("/api/generate", json={"model": settings.model, "keep_alive": 0})


async def ollama_version(settings: Settings) -> str:
    """
    Version string of the Ollama server, or "unknown" when it cannot be read.
    """
    try:
        async with httpx.AsyncClient(base_url=settings.ollama_url, timeout=10) as http:
            response = await http.get("/api/version")
            return str(response.json()["version"])
    except (httpx.HTTPError, KeyError, ValueError):
        return "unknown"


def git_revision() -> str:
    """
    The current git commit, with a "-dirty" suffix when the working tree has changes.
    """
    try:
        root = Path(__file__).resolve().parent
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
        return rev + ("-dirty" if dirty.strip() else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def prompts_digest(settings: Settings) -> str:
    """
    SHA-256 over the prompt files, identifying the prompt version used.
    """
    digest = hashlib.sha256()
    for path in sorted((settings.data_dir / "prompts").glob("*.md")):
        digest.update(path.name.encode() + path.read_bytes())
    return digest.hexdigest()


def write_run(
    out_dir: Path,
    settings: Settings,
    cases_path: Path,
    results: list[CaseResult],
    server_version: str = "unknown",
) -> None:
    """
    Write one model's results and the settings that produced them.

    Args:
        out_dir: The run folder.
        settings: Settings used for the run.
        cases_path: The cases file that was run.
        results: One result per case.
        server_version: Ollama version, recorded because it affects model behaviour.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(settings.model)
    with (out_dir / f"{stem}.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    meta = {
        "model": settings.model,
        "seed": settings.seed,
        "temperature": settings.temperature,
        "llm_budget": settings.llm_budget,
        "num_ctx": settings.num_ctx,
        "num_predict": settings.num_predict,
        "few_shot_count": FEW_SHOT_COUNT,
        "cases_sha256": cases_digest(cases_path),
        "prompts_sha256": prompts_digest(settings),
        "ollama_version": server_version,
        "git_revision": git_revision(),
        "date_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out_dir / f"{stem}.meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--models", nargs="+", required=True, help="Ollama model tags")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    parser.add_argument("--run-id", default=datetime.now(UTC).strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--limit", type=int, help="Run only the first N cases")
    parser.add_argument("--seed", type=int, default=0, help="Sampling seed (default 0)")
    parser.add_argument(
        "--budget",
        type=float,
        default=30.0,
        help="Seconds allowed per request, so slow models are judged on quality, not speed",
    )
    args = parser.parse_args(argv)

    cases = load_cases(args.cases)
    if args.limit:
        cases = cases[: args.limit]
    run_dir = args.out / args.run_id

    failed = []
    for model in args.models:
        settings = Settings(model=model, seed=args.seed, llm_budget=args.budget)
        print(f"== {model}: {len(cases)} cases", flush=True)
        try:
            results = await run_model(settings, cases)
        except RuntimeError as exc:
            print(f"   skipped: {exc}", file=sys.stderr)
            failed.append(model)
            continue
        finally:
            await unload(settings)
        write_run(run_dir, settings, args.cases, results, await ollama_version(settings))
        usable = sum(r.source == "llm" and bool(r.candidates) for r in results)
        print(f"   usable {usable}/{len(results)}", flush=True)

    if len(failed) == len(args.models):
        return 1
    report.write_report(run_dir, cases)
    print((run_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Results in {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
