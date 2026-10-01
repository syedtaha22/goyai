from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.base import LLMError
from app.main import create_app


class FakeLLM:
    def __init__(self, ready: bool = True, warmup_fails: bool = False) -> None:
        self._ready = ready
        self._warmup_fails = warmup_fails
        self.warmed = False
        self.closed = False

    @property
    def model(self) -> str:
        return "fake-model"

    async def generate(self, messages: list[dict[str, str]], schema: dict[str, Any], **kw: Any):
        return {}

    async def warmup(self) -> None:
        if self._warmup_fails:
            raise LLMError("no server")
        self.warmed = True

    async def is_ready(self) -> bool:
        return self._ready

    async def aclose(self) -> None:
        self.closed = True


def test_healthz_ok_and_warmup_runs():
    llm = FakeLLM()
    with TestClient(create_app(Settings(), llm)) as http:
        body = http.get("/healthz").json()
    assert body == {"status": "ok", "model": "fake-model", "model_available": True}
    assert llm.warmed and llm.closed


def test_healthz_degraded_when_model_missing():
    with TestClient(create_app(Settings(), FakeLLM(ready=False))) as http:
        body = http.get("/healthz").json()
    assert body["status"] == "degraded"
    assert body["model_available"] is False


def test_app_starts_when_warmup_fails():
    with TestClient(create_app(Settings(), FakeLLM(warmup_fails=True))) as http:
        assert http.get("/healthz").status_code == 200
