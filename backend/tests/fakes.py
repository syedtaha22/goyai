import asyncio
from typing import Any

from app.llm.base import LLMError


class FakeLLM:
    """
    Test double for LLMClient.

    Attributes:
        responses: Values returned by successive generate calls. An Exception instance is
            raised instead of returned. The last value repeats once the list is used up.
        calls: One dict per generate call, with the messages, schema and temperature.
        delay: Seconds each generate call sleeps, to simulate a slow model.
    """

    def __init__(
        self,
        ready: bool = True,
        warmup_fails: bool = False,
        responses: list[Any] | None = None,
        delay: float = 0.0,
    ) -> None:
        self._ready = ready
        self._warmup_fails = warmup_fails
        self.responses = responses if responses is not None else [{}]
        self.delay = delay
        self.calls: list[dict[str, Any]] = []
        self.warmed = False
        self.closed = False

    @property
    def model(self) -> str:
        return "fake-model"

    async def generate(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        *,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        self.calls.append({"messages": messages, "schema": schema, "temperature": temperature})
        if self.delay:
            await asyncio.sleep(self.delay)
        index = min(len(self.calls) - 1, len(self.responses) - 1)
        response = self.responses[index]
        if isinstance(response, Exception):
            raise response
        return response

    async def warmup(self) -> None:
        if self._warmup_fails:
            raise LLMError("no server")
        self.warmed = True

    async def is_ready(self) -> bool:
        return self._ready

    async def aclose(self) -> None:
        self.closed = True
