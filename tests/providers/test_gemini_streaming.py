import pytest

from alloy.models.gemini import GeminiBackend
from alloy.config import Config
from alloy import ConfigurationError


class _Chunk:
    def __init__(self, text: str):
        self.text = text


class _FakeGeminiClient:
    class aio:
        class models:
            @staticmethod
            async def generate_content_stream(*, model, contents, config=None):
                async def _gen():
                    for t in ["Hello ", "Gemini"]:
                        yield _Chunk(t)

                return _gen()


@pytest.mark.asyncio
async def test_gemini_astream_yields_text(monkeypatch):
    be = GeminiBackend()
    be._client_sync = _FakeGeminiClient()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
    cfg = Config(model="gemini-2.5-flash")
    aiter = await be.astream("prompt", tools=None, output_schema=None, config=cfg)
    out: list[str] = []
    async for chunk in aiter:
        out.append(chunk)
    assert "".join(out) == "Hello Gemini"


@pytest.mark.asyncio
async def test_gemini_astream_disallows_tools_and_schema(monkeypatch):
    be = GeminiBackend()
    be._client_sync = _FakeGeminiClient()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
    cfg = Config(model="gemini-2.5-flash")
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=[lambda: None], output_schema=None, config=cfg)
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)


def test_gemini_stream_yields_text(monkeypatch):
    be = GeminiBackend()

    class _SyncChunk:
        def __init__(self, text: str):
            self.text = text

    class _SyncClient:
        class models:
            @staticmethod
            def generate_content_stream(*, model, contents, config=None):
                return [_SyncChunk("Sync "), _SyncChunk("Gemini")]

    be._client_sync = _SyncClient()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
    cfg = Config(model="gemini-2.5-flash")
    chunks = list(be.stream("prompt", tools=None, output_schema=None, config=cfg))
    assert "".join(chunks) == "Sync Gemini"
