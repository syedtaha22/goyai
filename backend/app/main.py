from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import coloredlogs
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.fallback import ExampleBank
from app.llm.base import LLMClient
from app.llm.ollama import OllamaClient
from app.schemas import SuggestRequest, SuggestResponse
from app.suggest import Suggester
from app.tiles import Tile, TileBank, UnknownTileError


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

    tiles = TileBank.load(settings.data_dir / "tiles.json")
    examples = ExampleBank.load(settings.data_dir / "examples.json")
    suggester = Suggester(llm, tiles, examples, settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.llm = llm
        app.state.suggester = suggester
        # Load the model in the background so the API answers, via the fallback, meanwhile.
        suggester.start_warmup()
        yield
        await suggester.stop()
        await llm.aclose()

    app = FastAPI(title="Goyai backend", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/v1/tiles")
    async def list_tiles() -> list[Tile]:
        return tiles.tiles

    @app.post("/v1/suggest")
    async def suggest(req: SuggestRequest) -> SuggestResponse:
        try:
            return await suggester.suggest(req)
        except UnknownTileError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/healthz")
    async def healthz(request: Request) -> dict[str, object]:
        ready = await request.app.state.llm.is_ready()
        return {
            "status": "ok" if ready else "degraded",
            "model": request.app.state.llm.model,
            "model_available": ready,
            "model_loaded": request.app.state.suggester.loaded,
        }

    return app


app = create_app()
