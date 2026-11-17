from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import coloredlogs
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.engine import CandidateEngine
from app.fallback import ExampleBank
from app.llm.base import LLMClient
from app.llm.engine import LLMEngine
from app.llm.ollama import OllamaClient
from app.schemas import SuggestRequest, SuggestResponse
from app.suggest import Suggester
from app.tiles import Tile, TileBank, UnknownTileError


def create_app(settings: Settings | None = None, client: LLMClient | None = None) -> FastAPI:
    """
    Build the FastAPI application.

    Args:
        settings: Configuration. Defaults to the environment-derived settings.
        client: Model client for the language model engine. Giving one selects that engine.
            Otherwise the engine named in the settings is used.
    """
    settings = settings or get_settings()
    coloredlogs.install(
        level=settings.log_level,
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    tiles = TileBank.load(settings.data_dir / "tiles.json")
    examples = ExampleBank.load(settings.data_dir / "examples.json")

    engine: CandidateEngine
    if client is None and settings.engine == "transformer":
        from app.decoder.engine import TransformerEngine

        engine = TransformerEngine(settings)
    else:
        engine = LLMEngine(client or OllamaClient(settings), tiles, examples, settings)
    suggester = Suggester(engine, tiles, examples)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = engine
        app.state.suggester = suggester
        # Load the model in the background so the API answers, via the fallback, meanwhile.
        suggester.start_warmup()
        yield
        await suggester.stop()
        await engine.aclose()

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
        ready = await request.app.state.engine.is_ready()
        return {
            "status": "ok" if ready else "degraded",
            "model": request.app.state.engine.model,
            "model_available": ready,
            "model_loaded": request.app.state.suggester.loaded,
        }

    return app


app = create_app()
