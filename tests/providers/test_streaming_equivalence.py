import pytest

from alloy.config import Config
from alloy import ConfigurationError


class _OAIFakeStream:
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider,expected",
    [
        ("openai", "one two"),
        ("anthropic", "one two"),
        ("gemini", "one two"),
    ],
)
async def test_astream_equivalence(monkeypatch, provider, expected):
    if provider == "openai":
        from alloy.models.openai import OpenAIBackend

        be = OpenAIBackend()

        class _Resp:
            @staticmethod
            def stream(**kwargs):
                return _OAIFakeStream(
                    [
                        {"type": "response.output_text.delta", "delta": "one "},
                        {"type": "response.output_text.delta", "delta": "two"},
                    ]
                )

        be._client_async = type("C", (), {"responses": _Resp})()
        monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
        cfg = Config(model="gpt-5-mini")
        aiter = await be.astream("prompt", tools=None, output_schema=None, config=cfg)
    elif provider == "anthropic":
        from alloy.models.anthropic import AnthropicBackend

        be = AnthropicBackend()

        class _Stream:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            @property
            def text_stream(self):
                async def _gen():
                    for t in ["one ", "two"]:
                        yield t

                return _gen()

        be._client_async = type(
            "C", (), {"messages": type("M", (), {"stream": staticmethod(lambda **_: _Stream())})()}
        )()
        monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
        cfg = Config(model="claude-3")
        aiter = await be.astream("prompt", tools=None, output_schema=None, config=cfg)
    else:
        from alloy.models.gemini import GeminiBackend

        be = GeminiBackend()

        class _Chunk:
            def __init__(self, text: str):
                self.text = text

        async def _gen():
            for t in ["one ", "two"]:
                yield _Chunk(t)

        async def _generate_content_stream(**_kwargs):
            return _gen()

        be._client_sync = type(
            "C",
            (),
            {
                "aio": type(
                    "A",
                    (),
                    {
                        "models": type(
                            "M",
                            (),
                            {"generate_content_stream": staticmethod(_generate_content_stream)},
                        )()
                    },
                )()
            },
        )()
        monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
        cfg = Config(model="gemini-2.5-flash")
        aiter = await be.astream("prompt", tools=None, output_schema=None, config=cfg)

    parts: list[str] = []
    async for chunk in aiter:
        parts.append(chunk)
    assert "".join(parts) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["openai", "anthropic", "gemini"])
async def test_astream_gating_equivalence(monkeypatch, provider):
    if provider == "openai":
        from alloy.models.openai import OpenAIBackend

        be = OpenAIBackend()
        be._client_async = type("C", (), {"responses": object()})()
        monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
        cfg = Config(model="gpt-5-mini")
    elif provider == "anthropic":
        from alloy.models.anthropic import AnthropicBackend

        be = AnthropicBackend()
        be._client_async = type("C", (), {"messages": object()})()
        monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
        cfg = Config(model="claude-3")
    else:
        from alloy.models.gemini import GeminiBackend

        be = GeminiBackend()
        be._client_sync = object()
        monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
        cfg = Config(model="gemini-2.5-flash")

    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=[lambda: None], output_schema=None, config=cfg)
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)
