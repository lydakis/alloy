import pytest

from alloy.models.anthropic import AnthropicBackend
from alloy.config import Config
from alloy import ConfigurationError


class _FakeAnthropicStream:
    def __init__(self, chunks: list[str]):
        self._chunks = chunks

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    @property
    def text_stream(self):
        async def _gen():
            for c in self._chunks:
                yield c

        return _gen()


class _FakeAnthropicClient:
    class messages:
        @staticmethod
        def stream(**kwargs):
            return _FakeAnthropicStream(["Hi ", "there"])


@pytest.mark.asyncio
async def test_anthropic_astream_yields_text(monkeypatch):
    be = AnthropicBackend()
    be._client_async = _FakeAnthropicClient()
    monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
    cfg = Config(model="claude-3")
    aiter = await be.astream("prompt", tools=None, output_schema=None, config=cfg)
    out: list[str] = []
    async for chunk in aiter:
        out.append(chunk)
    assert "".join(out) == "Hi there"


@pytest.mark.asyncio
async def test_anthropic_astream_disallows_tools_and_schema(monkeypatch):
    be = AnthropicBackend()
    be._client_async = _FakeAnthropicClient()
    monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
    cfg = Config(model="claude-3")
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=[lambda: None], output_schema=None, config=cfg)
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)


def test_anthropic_stream_yields_text(monkeypatch):
    be = AnthropicBackend()

    class _SyncStream:
        def __init__(self, chunks):
            self._chunks = chunks

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        @property
        def text_stream(self):
            def _gen():
                for c in self._chunks:
                    yield c

            return _gen()

    class _SyncClient:
        class messages:
            @staticmethod
            def stream(**kwargs):
                return _SyncStream(["Hello ", "Claude"])

    be._client_sync = _SyncClient()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
    cfg = Config(model="claude-3")
    chunks = list(be.stream("prompt", tools=None, output_schema=None, config=cfg))
    assert "".join(chunks) == "Hello Claude"
