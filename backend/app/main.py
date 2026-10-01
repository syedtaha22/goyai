import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import coloredlogs
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.llm.base import LLMClient, LLMError
from app.llm.ollama import OllamaClient

logger = logging.getLogger("goyai")


def create_app(settings: Settings | None = None, client: LLMClient | None = None) -> FastAPI:
    """
    Build the FastAPI application.

    Args:
        settings: Configuration. Defaults to the environment-derived settings.
        client: Model client. Defaults to an OllamaClient built from the settings.
    """
    settings = settings or get_settings()
    coloredlogs.install(
        level=settings.log_level,
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    llm: LLMClient = client or OllamaClient(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.llm = llm
        try:
            await llm.warmup()
            logger.info("Model %s loaded", llm.model)
        except LLMError as exc:
            logger.warning("Warmup failed, requests will fall back until the model is up: %s", exc)
        yield
        await llm.aclose()

    app = FastAPI(title="Goyai backend", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/healthz")
    async def healthz(request: Request) -> dict[str, object]:
        ready = await request.app.state.llm.is_ready()
        return {
            "status": "ok" if ready else "degraded",
            "model": request.app.state.llm.model,
            "model_available": ready,
        }

    return app


app = create_app()
