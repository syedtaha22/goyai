import asyncio
import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

import coloredlogs
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.fallback import ExampleBank
from app.llm.base import LLMClient, LLMError
from app.llm.ollama import OllamaClient
from app.schemas import SuggestRequest, SuggestResponse
from app.tiles import Tile, TileBank, UnknownTileError

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

        async def warm() -> None:
            try:
                await llm.warmup()
                logger.info("Model %s loaded", llm.model)
            except LLMError as exc:
                logger.warning("Warmup failed, requests fall back until the model is up: %s", exc)

        # Warm in the background so the API answers, via the fallback, while the model loads.
        warmup_task = asyncio.create_task(warm())
        yield
        warmup_task.cancel()
        with suppress(asyncio.CancelledError):
            await warmup_task
        await llm.aclose()

    app = FastAPI(title="Goyai backend", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    tiles = TileBank.load(settings.data_dir / "tiles.json")
    examples = ExampleBank.load(settings.data_dir / "examples.json")

    @app.get("/v1/tiles")
    async def list_tiles() -> list[Tile]:
        return tiles.tiles

    @app.post("/v1/suggest")
    async def suggest(req: SuggestRequest) -> SuggestResponse:
        started = time.perf_counter()
        try:
            selected = tiles.resolve(req.tiles, req.profile.custom_labels)
        except UnknownTileError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        candidates = examples.suggest(selected, req.n, req.exclude)
        return SuggestResponse(
            candidates=candidates,
            source="fallback",
            latency_ms=round((time.perf_counter() - started) * 1000),
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
