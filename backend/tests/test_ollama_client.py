import json

import httpx
import pytest

from app.config import Settings
from app.llm.base import LLMError
from app.llm.ollama import OllamaClient


def make_client(handler, **overrides) -> OllamaClient:
    settings = Settings(model="test-model", **overrides)
    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url=settings.ollama_url
    )
    return OllamaClient(settings, http)


@pytest.mark.anyio
async def test_generate_sends_schema_and_parses_json():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": '{"candidates": []}'}})

    client = make_client(handler)
    schema = {"type": "object"}
    out = await client.generate([{"role": "user", "content": "hi"}], schema, temperature=0.8)

    assert out == {"candidates": []}
    body = seen["body"]
    assert body["model"] == "test-model"
    assert body["format"] == schema
    assert body["think"] is False
    assert body["stream"] is False
    assert body["options"]["temperature"] == 0.8


@pytest.mark.anyio
async def test_generate_raises_on_invalid_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "not json"}})

    client = make_client(handler)
    with pytest.raises(LLMError):
        await client.generate([], {})


@pytest.mark.anyio
async def test_generate_raises_on_server_error():
    client = make_client(lambda request: httpx.Response(500))
    with pytest.raises(LLMError):
        await client.generate([], {})


@pytest.mark.anyio
async def test_is_ready_matches_model_name():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "test-model:latest"}]})

    assert await make_client(handler).is_ready() is True


@pytest.mark.anyio
async def test_is_ready_false_when_model_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "other:1b"}]})

    assert await make_client(handler).is_ready() is False


@pytest.mark.anyio
async def test_is_ready_false_when_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    assert await make_client(handler).is_ready() is False


@pytest.mark.anyio
async def test_warmup_raises_when_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    with pytest.raises(LLMError):
        await make_client(handler).warmup()
