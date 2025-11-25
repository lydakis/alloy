import pytest

from alloy.config import Config
from alloy import ConfigurationError, tool


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

        class _Resp:
            @staticmethod
            def stream(**kwargs):
                return _OAIFakeStream(
                    [
                        {"type": "response.output_text.delta", "delta": "chunk"},
                    ]
                )

        be._client_async = type("C", (), {"responses": _Resp})()
        monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
        cfg = Config(model="gpt-5-mini")
        _tool_calls: list[str] = []

        @tool
        def noop() -> str:
            _tool_calls.append("run")
            return "ok"

        aiter = await be.astream("prompt", tools=[noop], output_schema=None, config=cfg)
        chunks = []
        async for ch in aiter:
            chunks.append(ch)
        assert "".join(chunks) == "chunk"
        assert _tool_calls
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
                    yield "chunk"

                return _gen()

            async def get_final_message(self):
                from anthropic.types import Message

                return Message.model_validate(
                    {
                        "id": "msg",
                        "content": [{"type": "text", "text": "chunk"}],
                        "model": "claude-3-sonnet",
                        "role": "assistant",
                        "stop_reason": "end_turn",
                        "type": "message",
                        "usage": {"input_tokens": 1, "output_tokens": 1},
                    }
                )

        be._client_async = type(
            "C", (), {"messages": type("M", (), {"stream": staticmethod(lambda **_: _Stream())})()}
        )()
        monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
        cfg = Config(model="claude-3")
        _tool_calls: list[str] = []

        @tool
        def noop() -> str:
            _tool_calls.append("run")
            return "ok"

        aiter = await be.astream("prompt", tools=[noop], output_schema=None, config=cfg)
        chunks: list[str] = []
        async for ch in aiter:
            chunks.append(ch)
        assert "".join(chunks) == "chunk"
        assert _tool_calls
    else:
        from alloy.models.gemini import GeminiBackend

        be = GeminiBackend()

        class _Part:
            def __init__(self, text=None, function_call=None, function_response=None):
                self.text = text
                self.function_call = function_call
                self.function_response = function_response

        class _Types:
            class Schema:
                def __init__(self, **kwargs):
                    self.kw = kwargs

            class FunctionDeclaration:
                def __init__(self, **kwargs):
                    self.kw = kwargs

            class Tool:
                def __init__(self, **kwargs):
                    self.kw = kwargs

            class AutomaticFunctionCallingConfig:
                def __init__(self, **kwargs):
                    self.kw = kwargs

            class FunctionCallingConfig:
                def __init__(self, **kwargs):
                    self.kw = kwargs

            class ToolConfig:
                def __init__(self, **kwargs):
                    self.kw = kwargs

            class Content:
                def __init__(self, role, parts):
                    self.role = role
                    self.parts = parts

            class Part:
                @staticmethod
                def from_text(text: str):
                    return _Part(text=text)

                @staticmethod
                def from_function_response(name: str, response):
                    return _Part(function_response={"name": name, "response": response})

        def _tool_chunk():
            fc = type("_FC", (), {"name": "noop", "args": {}})()
            envelope = type("_Envelope", (), {"function_call": fc, "name": "noop"})()
            part = _Part(function_call=fc)
            content = _Types.Content(role="assistant", parts=[part])
            candidate = type("_Cand", (), {"content": content})()
            return type(
                "_Resp",
                (),
                {
                    "text": "",
                    "function_calls": [envelope],
                    "candidates": [candidate],
                    "parsed": None,
                },
            )()

        def _text_chunk():
            part = _Part(text="chunk")
            content = _Types.Content(role="assistant", parts=[part])
            candidate = type("_Cand", (), {"content": content})()
            return type(
                "_Resp",
                (),
                {
                    "text": "chunk",
                    "function_calls": None,
                    "candidates": [candidate],
                    "parsed": None,
                },
            )()

        class _AsyncStream:
            def __init__(self, chunks):
                self._iter = iter(chunks)

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration as exc:
                    raise StopAsyncIteration from exc

            async def aclose(self):
                return None

        class _AsyncModels:
            def __init__(self):
                self.calls = 0

            async def generate_content_stream(self, *, model, contents, config=None):
                self.calls += 1
                if self.calls == 1:
                    return _AsyncStream([_tool_chunk()])
                if self.calls == 2:
                    return _AsyncStream([_text_chunk()])
                raise AssertionError("unexpected extra async stream")

        be._client_sync = type(
            "_Client",
            (),
            {
                "aio": type("_Aio", (), {"models": _AsyncModels()})(),
                "models": type("_Sync", (), {"generate_content_stream": lambda **_: []})(),
            },
        )()
        be._Types = _Types
        monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
        cfg = Config(model="gemini-2.5-flash")
        _tool_calls: list[str] = []

        @tool
        def noop() -> str:
            _tool_calls.append("run")
            return "ok"

        aiter = await be.astream("prompt", tools=[noop], output_schema=None, config=cfg)
        chunks: list[str] = []
        async for ch in aiter:
            chunks.append(ch)
        assert "".join(chunks) == "chunk"
        assert _tool_calls
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)
