# Goyai backend

FastAPI service that sits between the tile board and a locally hosted language model. The model
runs in [Ollama](https://ollama.com) on localhost, so message content stays on the machine.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ollama pull qwen3.5:4b
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
curl localhost:8000/healthz
```

`/healthz` reports `"status": "ok"` when Ollama is reachable and the configured model is pulled,
and `"degraded"` otherwise. `model_loaded` is `true` once the model has been loaded into memory,
which happens in the background after startup.

## API

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Model server status |
| `GET /v1/tiles` | The tile bank (204 tiles) |
| `POST /v1/suggest` | Candidate sentences for a tile selection |

```bash
curl -s localhost:8000/v1/suggest -H 'Content-Type: application/json' \
  -d '{"tiles": ["person_i_me", "action_want", "food_water"]}'
```

`POST /v1/suggest` request fields:

- `tiles`: 1 to 6 tile IDs, in selection order.
- `profile`: optional. `gender` selects gendered Urdu forms, and `custom_labels` supplies
  labels for personalization tiles.
- `exclude`: Urdu sentences already shown, which are not returned again.
- `n`: number of candidates, 1 to 5. Default 3.
- `mode`: `default`, or `different` to ask for more varied candidates.

Response fields:

- `candidates`: ranked list, each with `urdu`, `english` and `style` (`urdu` or `code_mixed`).
- `source`: `llm` or `fallback`.
- `model`: model name when `source` is `llm`, otherwise `null`.
- `latency_ms`: time taken to produce the candidates.

Unknown tile IDs, and invalid request fields, return 422.

## How suggestions are produced

1. The selected tiles are looked up in the tile bank.
2. The model receives a system prompt, the four curated examples that overlap the selection most
   (as earlier conversation turns), and the selected tiles with their Urdu and English labels.
   The prompt texts are the markdown files in [data/prompts/](data/prompts/), where
   `{{NAME}}` marks the parts the code fills in.
   The speaker's gender, when given, selects the verb forms. For `mode: "different"` the
   sentences already shown are included and the sampling temperature is higher.
3. The response is cleaned: candidates that contain notes, brackets, hidden characters, too
   little Urdu script or a non-English translation are dropped, as are repeats and anything in
   `exclude`. Sentence-final punctuation is normalized, and a candidate containing Latin letters
   is marked `code_mixed`.
4. If the first attempt gives nothing usable, the request is retried once.
5. If the model is not loaded, errors out, or exceeds `GOYAI_LLM_BUDGET`, the curated example
   bank answers and `source` is `fallback`.

## Data

[data/tiles.json](data/tiles.json) holds the tile bank. Each tile has a stable `tile_id`
(`<category>_<english>`), a category, Urdu and English labels, and an `arasaac_id` that is
`null` until the pictogram is matched. [data/examples.json](data/examples.json) holds curated
tile selections with reference sentences, used as few-shot examples in the prompt and as the
fallback when the language model is unavailable.

## Evaluation

[evaluation/cases.jsonl](evaluation/cases.jsonl) holds the evaluation cases. Each case has a tile
selection, one or more acceptable Urdu sentences (`references`), an English gloss, and an
optional speaker gender. The `urdu` cases use monolingual Urdu. The `code_mixed` cases use Urdu with 
English words, and give the English words in Latin script in the first reference and in Urdu script 
in the others. No case reuses the tile selection of a curated example in [data/examples.json](data/examples.json).

Run the pipeline for one or more models, from `backend/`:

```bash
python -m evaluation.run --models qwen3.5:4b gemma3:4b --run-id my-run
```

Options: `--limit N` runs the first N cases, `--seed` sets the sampling seed (default 0),
`--budget` sets the seconds allowed per request (default 30, so slow models are compared on
quality). Results go to `evaluation/results/<run id>/`, which is git-ignored:

- `<model>.jsonl`: the candidates and latency for each case.
- `<model>.meta.json`: model, seed, temperature, token limits, a hash of the cases file and of
  the prompt files, the Ollama version, the git commit, and the date.
- `summary.md` and `summary.json`: the automatic metrics, for all cases and for each split.
- `ratings.csv` and `ratings_key.csv`: the rating sheet and its key (see below).

`python -m evaluation.report <run folder>` rebuilds the summary and rating sheet from the
results. With `--sample N` the rating sheet covers a seeded sample of N cases, drawn in
proportion from each split, while the summary still covers every case.

Automatic metrics, as fractions of all cases:

- `usable`: the model returned at least one candidate that passed cleaning.
- `exact@k`: a reference sentence appears among the top k candidates, ignoring case, spacing and
  punctuation. This is a lower bound, because a correct sentence that is not listed as a
  reference does not count. Whether a sentence is correct is judged by the ratings.
- `code-mixed offered`: at least one candidate is marked `code_mixed`.
- `candidates`: mean number of candidates for usable responses.
- `p50 ms` and `p95 ms`: latency percentiles.

A response that falls back to the curated examples counts as a miss for every metric.

Rating sheet: `ratings.csv` lists each distinct sentence once, in shuffled order, with the model
names hidden. It contains the top three candidates of every model and one reference sentence per
case as a control. Raters fill in `meaning_ok` (1 or 0), `fluency_1to5`, `gender_ok` (1, 0 or
`NA`), `code_mix_natural_1to5` (code-mixed cases only) and `notes`. `ratings_key.csv` maps each
row to the models and ranks that produced it. Then:

```bash
python -m evaluation.score_ratings <run folder>
```

prints the mean ratings per model, with the references as the `reference` row.

## Configuration

Settings are read from environment variables prefixed with `GOYAI_`, or from a local `.env` file
(git-ignored). Copy [.env.example](.env.example) to `.env` to start. See
[app/config.py](app/config.py) for all options.

| Variable | Default | Meaning |
|---|---|---|
| `GOYAI_MODEL` | `qwen3.5:4b` | Ollama model tag |
| `GOYAI_OLLAMA_URL` | `http://localhost:11434` | Ollama server |
| `GOYAI_REQUEST_TIMEOUT` | `20` | Seconds per model request |
| `GOYAI_KEEP_ALIVE` | `30m` | How long the model stays loaded |
| `GOYAI_TEMPERATURE` | `0.3` | Sampling temperature for a first request |
| `GOYAI_TEMPERATURE_DIFFERENT` | `0.8` | Sampling temperature for `mode: "different"` |
| `GOYAI_LLM_BUDGET` | `8` | Seconds a request may spend on the model before the fallback answers |
| `GOYAI_LOG_LEVEL` | `INFO` | Log verbosity |
| `GOYAI_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed browser origins |

## Tests

```bash
pytest
ruff check .
```
