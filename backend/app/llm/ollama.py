from typing import Any

import httpx

from app.config import Settings
from app.llm.base import LLMError
from app.llm.jsonutil import extract_json_object


class OllamaClient:
    """
    LLMClient implementation that talks to a local Ollama server over HTTP.
    """

    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._http = http or httpx.AsyncClient(base_url=settings.ollama_url)

    @property
    def model(self) -> str:
        return self._settings.model

    async def generate(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        *,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        s = self._settings
        payload = {
            "model": s.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "format": schema,
            "keep_alive": s.keep_alive,
            "options": {
                "temperature": temperature,
                "num_ctx": s.num_ctx,
                "num_predict": s.num_predict,
            },
        }
        try:
            resp = await self._http.post("/api/chat", json=payload, timeout=s.request_timeout)
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            return extract_json_object(content)
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama request failed: {exc!r}") from exc
        except (KeyError, ValueError) as exc:
            raise LLMError(f"Ollama returned unusable output: {exc!r}") from exc

    async def warmup(self) -> None:
        s = self._settings
        payload = {"model": s.model, "keep_alive": s.keep_alive}
        try:
            resp = await self._http.post("/api/generate", json=payload, timeout=s.warmup_timeout)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama warmup failed: {exc!r}") from exc

    async def is_ready(self) -> bool:
        try:
            resp = await self._http.get("/api/tags", timeout=3.0)
            resp.raise_for_status()
            names = {m["name"] for m in resp.json().get("models", [])}
        except (httpx.HTTPError, KeyError, ValueError):
            return False
        wanted = self._settings.model
        return wanted in names or f"{wanted}:latest" in names

    async def aclose(self) -> None:
        await self._http.aclose()
