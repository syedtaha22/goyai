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
