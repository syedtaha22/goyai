from typing import Protocol

from app.schemas import Candidate, SuggestRequest
from app.tiles import Tile


class EngineError(Exception):
    """
    Raised when an engine cannot load or fails to produce output.
    """


class CandidateEngine(Protocol):
    """
    Interface of every source of candidate sentences.

    The suggester depends only on this protocol, so the model behind it can be replaced without
    touching request handling or the fallback.
    """

    @property
    def model(self) -> str:
        """
        Name of the model that produces the candidates.
        """
        ...

    async def candidates(self, selected: list[Tile], req: SuggestRequest) -> list[Candidate]:
        """
        Produce clean candidate sentences for a tile selection.

        Args:
            selected: The resolved tiles in selection order.
            req: The validated request, which carries the profile, exclusions and mode.

        Returns:
            At most req.n candidates, possibly none.
        """
        ...

    async def warmup(self) -> None:
        """
        Load the model so the first real request does not pay the load cost.

        Raises:
            EngineError: If the model cannot be loaded.
        """
        ...

    async def is_ready(self) -> bool:
        """
        Return True when the model is available to load or already loaded.
        """
        ...

    async def aclose(self) -> None:
        """
        Release resources.
        """
        ...
