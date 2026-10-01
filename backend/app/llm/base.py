from typing import Any, Protocol


class LLMError(Exception):
    """
    Raised when the model server is unreachable, times out, or returns unusable output.
    """


class LLMClient(Protocol):
    """
    Interface every model backend implements.

    The rest of the application depends only on this protocol, so the model server can be
    replaced without touching prompt construction or post-processing.
    """

    @property
    def model(self) -> str:
        """
        Name of the model this client sends requests to.
        """
        ...

    async def generate(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        *,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """
        Run one chat completion constrained to a JSON schema.

        Args:
            messages: Chat messages, each with "role" and "content".
            schema: JSON schema the response must satisfy.
            temperature: Sampling temperature.

        Returns:
            The parsed JSON object produced by the model.

        Raises:
            LLMError: If the server fails, times out, or the output is not valid JSON.
        """
        ...

    async def warmup(self) -> None:
        """
        Load the model into memory so the first real request does not pay the load cost.

        Raises:
            LLMError: If the model cannot be loaded.
        """
        ...

    async def is_ready(self) -> bool:
        """
        Return True when the server is reachable and the configured model is available.
        """
        ...

    async def aclose(self) -> None:
        """
        Release network resources.
        """
        ...
