from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Backend configuration.

    Every field can be overridden with an environment variable prefixed with GOYAI_
    (for example GOYAI_MODEL) or with an entry in a local .env file.
    """

    model_config = SettingsConfigDict(env_prefix="GOYAI_", env_file=".env", extra="ignore")

    model: str = "qwen3.5:4b"
    ollama_url: str = "http://localhost:11434"

    # Seconds to wait for a single model response before giving up.
    request_timeout: float = 20.0
    # Seconds allowed for the startup warmup, which may include loading weights into VRAM.
    warmup_timeout: float = 120.0
    # How long Ollama keeps the model resident after the last request.
    keep_alive: str = "30m"

    # Context window and generation cap. Both stay small to bound latency.
    num_ctx: int = 4096
    num_predict: int = 512

    log_level: str = "INFO"

    # Origins allowed to call the API from a browser (the Next.js dev server by default).
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached Settings instance.
    """
    return Settings()
