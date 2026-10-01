import asyncio
import logging
import time
from contextlib import suppress

from app.config import Settings
from app.fallback import ExampleBank
from app.llm.base import LLMClient, LLMError
from app.postprocess import clean_candidates
from app.prompt import (
    FEW_SHOT_COUNT,
    PromptTemplates,
    build_messages,
    candidates_schema,
    select_examples,
)
from app.schemas import Candidate, SuggestRequest, SuggestResponse
from app.tiles import Tile, TileBank

logger = logging.getLogger("goyai")

# Attempts at getting usable candidates from the model before falling back.
LLM_ATTEMPTS = 2


class Suggester:
    """
    Produces candidate sentences for a tile selection.

    Candidates come from the language model when it is loaded and returns usable output. In every
    other case the curated example bank answers, so a request always gets a response.
    """

    def __init__(
        self, llm: LLMClient, tiles: TileBank, examples: ExampleBank, settings: Settings
    ) -> None:
        self._llm = llm
        self._tiles = tiles
        self._examples = examples
        self._settings = settings
        self._templates = PromptTemplates.load(settings.data_dir / "prompts")
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
            await self._llm.warmup()
        except LLMError as exc:
            logger.warning("Warmup failed, requests fall back until the model is up: %s", exc)
            return
        self._loaded = True
        logger.info("Model %s loaded", self._llm.model)

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
            candidates = await self._from_model(selected, req)
        else:
            self.start_warmup()
        if not candidates:
            source = "fallback"
            candidates = self._examples.suggest(selected, req.n, req.exclude)

        return SuggestResponse(
            candidates=candidates,
            source=source,
            model=self._llm.model if source == "llm" else None,
            latency_ms=round((time.perf_counter() - started) * 1000),
        )

    async def _from_model(self, selected: list[Tile], req: SuggestRequest) -> list[Candidate]:
        s = self._settings
        resolved = self._tiles.resolve
        shots = [
            (resolved(ex.tiles), ex)
            for ex in select_examples(
                self._examples.examples, {t.tile_id for t in selected}, FEW_SHOT_COUNT
            )
        ]
        messages = build_messages(
            self._templates,
            selected,
            n=req.n,
            gender=req.profile.gender,
            exclude=req.exclude,
            shots=shots,
        )
        temperature = s.temperature_different if req.mode == "different" else s.temperature
        schema = candidates_schema(req.n)

        try:
            async with asyncio.timeout(s.llm_budget):
                for attempt in range(1, LLM_ATTEMPTS + 1):
                    try:
                        raw = await self._llm.generate(messages, schema, temperature=temperature)
                    except LLMError as exc:
                        logger.warning("Model call failed (attempt %d): %s", attempt, exc)
                        continue
                    candidates = clean_candidates(raw, req.n, req.exclude)
                    if candidates:
                        return candidates
                    logger.warning("Model returned no usable candidates (attempt %d)", attempt)
        except TimeoutError:
            logger.warning("Model exceeded the %.1f s budget", s.llm_budget)
        return []
