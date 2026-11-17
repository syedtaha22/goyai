import asyncio
import logging

from app.config import Settings
from app.engine import EngineError
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
from app.schemas import Candidate, SuggestRequest
from app.tiles import Tile, TileBank

logger = logging.getLogger("goyai")

# Attempts at getting usable candidates from the model before giving up.
LLM_ATTEMPTS = 2


class LLMEngine:
    """
    CandidateEngine that prompts a language model served by an LLMClient.
    """

    def __init__(
        self, client: LLMClient, tiles: TileBank, examples: ExampleBank, settings: Settings
    ) -> None:
        self._client = client
        self._tiles = tiles
        self._examples = examples
        self._settings = settings
        self._templates = PromptTemplates.load(settings.data_dir / "prompts")

    @property
    def model(self) -> str:
        return self._client.model

    async def warmup(self) -> None:
        try:
            await self._client.warmup()
        except LLMError as exc:
            raise EngineError(str(exc)) from exc

    async def is_ready(self) -> bool:
        return await self._client.is_ready()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def candidates(self, selected: list[Tile], req: SuggestRequest) -> list[Candidate]:
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
                        raw = await self._client.generate(messages, schema, temperature=temperature)
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
