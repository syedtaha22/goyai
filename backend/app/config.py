from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Backend configuration.

    Every field can be overridden with an environment variable prefixed with GOYAI_
    (for example GOYAI_MODEL) or with an entry in a local .env file.
    """

    model_config = SettingsConfigDict(env_prefix="GOYAI_", env_file=".env", extra="ignore")

    # Which engine produces the sentences: the in-process transformer or the Ollama model.
    engine: Literal["transformer", "llm"] = "transformer"

    # Folder with the transformer weights (transformer.pt) and tokenizer (urdu_bpe.model).
    decoder_dir: Path = Path(__file__).resolve().parent.parent / "models" / "transformer"
    # "auto" picks CUDA when it is available and the CPU otherwise.
    decoder_device: str = "auto"
    # CPU threads for the decoder. Left unset, torch uses every core.
    decoder_threads: int | None = 2
    # Run the CPU decoder with 8-bit weights, which roughly halves its time.
    decoder_quantize: bool = True
    decoder_max_new: int = 40
    decoder_length_alpha: float = 0.7

    model: str = "qwen3.5:4b"
    ollama_url: str = "http://localhost:11434"

    # Seconds to wait for a single model response before giving up.
    request_timeout: float = 20.0
    # Seconds allowed for the startup warmup, which may include loading weights into VRAM.
    warmup_timeout: float = 120.0
    # How long Ollama keeps the model resident after the last request.
    keep_alive: str = "30m"

    # Sampling temperatures: a first request is conservative, "different" is more varied.
    temperature: float = 0.3
    temperature_different: float = 0.8
    # Total seconds a request may spend on the model, retries included, before the fallback answers.
    llm_budget: float = 8.0

    # Fixed sampling seed for reproducible runs. Left unset, sampling is random.
    seed: int | None = None

    # Context window and generation cap. Both stay small to bound latency.
    num_ctx: int = 4096
    num_predict: int = 512

    log_level: str = "INFO"

    # Folder holding tiles.json and examples.json.
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"

    # Origins allowed to call the API from a browser (the Next.js dev server by default).
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached Settings instance.
    """
    return Settings()
