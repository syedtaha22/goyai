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
and `"degraded"` otherwise.

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

## Data

[data/tiles.json](data/tiles.json) holds the tile bank. Each tile has a stable `tile_id`
(`<category>_<english>`), a category, Urdu and English labels, and an `arasaac_id` that is
`null` until the pictogram is matched. [data/examples.json](data/examples.json) holds curated
tile selections with reference sentences, used when the language model is unavailable.

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
| `GOYAI_LOG_LEVEL` | `INFO` | Log verbosity |
| `GOYAI_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed browser origins |

## Tests

```bash
pytest
ruff check .
```
