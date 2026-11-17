import asyncio
import logging
import time
from contextlib import suppress

from app.engine import CandidateEngine, EngineError
from app.fallback import ExampleBank
from app.schemas import Candidate, SuggestRequest, SuggestResponse
from app.tiles import TileBank

logger = logging.getLogger("goyai")


class Suggester:
    """
    Produces candidate sentences for a tile selection.

    Candidates come from the engine when its model is loaded and returns usable output. In every
    other case the curated example bank answers, so a request always gets a response.
    """

    def __init__(self, engine: CandidateEngine, tiles: TileBank, examples: ExampleBank) -> None:
        self._engine = engine
        self._tiles = tiles
        self._examples = examples
        self._loaded = False
        self._warmup_task: asyncio.Task[None] | None = None

    @property
    def loaded(self) -> bool:
        """
        True once the model has been loaded and requests are sent to it.
        """
        return self._loaded

    def start_warmup(self) -> None:
        """
        Start loading the model in the background unless it is loaded or already loading.
        """
        if self._loaded or (self._warmup_task and not self._warmup_task.done()):
            return
        self._warmup_task = asyncio.create_task(self.warm())

    async def warm(self) -> None:
        """
        Load the model and, on success, start sending requests to it.

        A failure is logged and leaves the suggester on the fallback.
        """
        try:
            await self._engine.warmup()
        except EngineError as exc:
            logger.warning("Warmup failed, requests fall back until the model is up: %s", exc)
            return
        self._loaded = True
        logger.info("Model %s loaded", self._engine.model)

    async def stop(self) -> None:
        """
        Cancel any warmup still running.
        """
        if self._warmup_task:
            self._warmup_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._warmup_task

    async def suggest(self, req: SuggestRequest) -> SuggestResponse:
        """
        Produce candidate sentences for a request.

        Args:
            req: The validated request.

        Returns:
            The ranked candidates, with source "llm" when the model produced them and "fallback"
            otherwise.

        Raises:
            UnknownTileError: If the request names tiles that are not in the tile bank.
        """
        started = time.perf_counter()
        selected = self._tiles.resolve(req.tiles, req.profile.custom_labels)

        candidates: list[Candidate] = []
        source = "llm"
        if self._loaded:
            candidates = await self._engine.candidates(selected, req)
        else:
            self.start_warmup()
        if not candidates:
            source = "fallback"
            candidates = self._examples.suggest(selected, req.n, req.exclude)

        return SuggestResponse(
            candidates=candidates,
            source=source,
            model=self._engine.model if source == "llm" else None,
            latency_ms=round((time.perf_counter() - started) * 1000),
        )
