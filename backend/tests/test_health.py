import time

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.fakes import FakeLLM


def test_healthz_ok_and_warmup_runs():
    llm = FakeLLM()
    with TestClient(create_app(Settings(), llm)) as http:
        body = http.get("/healthz").json()
        for _ in range(50):
            if llm.warmed:
                break
            time.sleep(0.02)
    assert body["status"] == "ok"
    assert body["model"] == "fake-model"
    assert body["model_available"] is True
    assert llm.warmed and llm.closed


def test_healthz_reports_model_loaded():
    with TestClient(create_app(Settings(), FakeLLM())) as http:
        for _ in range(50):
            if http.get("/healthz").json()["model_loaded"]:
                break
            time.sleep(0.02)
        assert http.get("/healthz").json()["model_loaded"] is True


def test_healthz_not_loaded_when_warmup_fails():
    with TestClient(create_app(Settings(), FakeLLM(warmup_fails=True))) as http:
        time.sleep(0.1)
        assert http.get("/healthz").json()["model_loaded"] is False


def test_healthz_degraded_when_model_missing():
    with TestClient(create_app(Settings(), FakeLLM(ready=False))) as http:
        body = http.get("/healthz").json()
    assert body["status"] == "degraded"
    assert body["model_available"] is False


def test_app_starts_when_warmup_fails():
    with TestClient(create_app(Settings(), FakeLLM(warmup_fails=True))) as http:
        assert http.get("/healthz").status_code == 200
