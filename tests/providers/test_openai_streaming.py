import pytest

from alloy.models.openai import OpenAIBackend
from alloy.config import Config
from alloy import ConfigurationError


class _FakeStream:
    def __init__(self, events):
        self._events = events

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def __aiter__(self):
        async def _gen():
            for ev in self._events:
                yield ev

        return _gen()


class _FakeResponses:
    @staticmethod
    def stream(**kwargs):
        events = [
            {"type": "response.output_text.delta", "delta": "Hello "},
            {"type": "response.output_text.delta", "delta": "world"},
        ]
        return _FakeStream(events)


class _FakeClient:
    responses = _FakeResponses


@pytest.mark.asyncio
async def test_openai_astream_yields_text(monkeypatch):
    be = OpenAIBackend()
    be._client_async = _FakeClient()
    monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
    cfg = Config(model="gpt-5-mini")
    aiter = await be.astream("prompt", tools=None, output_schema=None, config=cfg)
    out: list[str] = []
    async for chunk in aiter:
        out.append(chunk)
    assert "".join(out) == "Hello world"


@pytest.mark.asyncio
async def test_openai_astream_disallows_schema(monkeypatch):
    be = OpenAIBackend()
    monkeypatch.setattr(be, "_get_async_client", lambda: _FakeClient())
    cfg = Config(model="gpt-5-mini")
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)


def test_openai_stream_yields_text(monkeypatch):
    be = OpenAIBackend()

    class _SyncFakeResponses:
        @staticmethod
        def stream(**kwargs):
            events = [
                {"type": "response.output_text.delta", "delta": "Sync "},
                {"type": "response.output_text.delta", "delta": "stream"},
            ]

            class _Ctx:
                def __enter__(self_inner):
                    return iter(events)

                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            return _Ctx()

    class _SyncFakeClient:
        responses = _SyncFakeResponses

    be._client_sync = _SyncFakeClient()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
    cfg = Config(model="gpt-5-mini")
    chunks = list(be.stream("prompt", tools=None, output_schema=None, config=cfg))
    assert "".join(chunks) == "Sync stream"


def test_openai_stream_disallows_schema(monkeypatch):
    be = OpenAIBackend()
    be._client_sync = object()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
    cfg = Config(model="gpt-5-mini")
    with pytest.raises(ConfigurationError):
        be.stream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)
