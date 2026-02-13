import pytest

from alloy.models.gemini import GeminiBackend
from alloy.config import Config
from alloy import ConfigurationError, tool


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
        def __init__(self, role: str, parts: list[object]):
            self.role = role
            self.parts = parts

    class Part:
        @staticmethod
        def from_text(text: str):
            return _Part(text=text)

        @staticmethod
        def from_function_response(name: str, response):
            return _Part(function_response={"name": name, "response": response})


class _Part:
    def __init__(
        self,
        text: str | None = None,
        function_call: object | None = None,
        function_response: object | None = None,
    ):
        self.text = text
        self.function_call = function_call
        self.function_response = function_response


class _FunctionCall:
    def __init__(self, name: str, args: dict[str, object]):
        self.name = name
        self.args = args


class _FunctionCallEnvelope:
    def __init__(self, name: str, args: dict[str, object]):
        self.function_call = _FunctionCall(name, args)
        self.name = name


class _Candidate:
    def __init__(self, content: object):
        self.content = content


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


def test_gemini_stream_disallows_schema(monkeypatch):
    be = GeminiBackend()
    be._client_sync = object()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)
    cfg = Config(model="gemini-2.5-flash")
    with pytest.raises(ConfigurationError):
        be.stream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)


class _FakeStream:
    def __init__(self, chunks: list[object]):
        self._chunks = chunks

    def __iter__(self):
        return iter(self._chunks)

    def close(self):
        return None


class _FakeAsyncStream:
    def __init__(self, chunks: list[object]):
        self._chunks = chunks
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


def _tool_call_chunk() -> object:
    fc = _FunctionCallEnvelope("fetch_fact", {})
    part = _Part(function_call=fc.function_call)
    content = _Types.Content(role="assistant", parts=[part])
    candidate = _Candidate(content)
    chunk = type(
        "_Resp",
        (),
        {
            "text": "",
            "function_calls": [fc],
            "candidates": [candidate],
            "parsed": None,
        },
    )
    return chunk()


def _text_chunk(text: str) -> object:
    part = _Part(text=text)
    content = _Types.Content(role="assistant", parts=[part])
    candidate = _Candidate(content)
    chunk = type(
        "_Resp",
        (),
        {
            "text": text,
            "function_calls": None,
            "candidates": [candidate],
            "parsed": None,
        },
    )
    return chunk()


def test_gemini_stream_with_tools_executes(monkeypatch):
    calls: list[str] = []

    @tool
    def fetch_fact() -> str:
        calls.append("run")
        return "tool says hi"

    class _Models:
        def __init__(self):
            self.calls = 0

        def generate_content_stream(self, *, model, contents, config=None):
            self.calls += 1
            if self.calls == 1:
                return _FakeStream([_tool_call_chunk()])
            if self.calls == 2:
                return _FakeStream([_text_chunk("Summary: tool says hi")])
            raise AssertionError("unexpected extra stream invocation")

    class _Client:
        def __init__(self):
            self.models = _Models()

    be = GeminiBackend()
    be._client_sync = _Client()
    be._Types = _Types
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)

    cfg = Config(model="gemini-2.5-flash")
    chunks = list(
        be.stream(
            "Use the fetch_fact tool to get info.",
            tools=[fetch_fact],
            output_schema=None,
            config=cfg,
        )
    )

    assert "Summary: tool says hi" == "".join(chunks)
    assert calls == ["run"]


@pytest.mark.asyncio
async def test_gemini_astream_with_tools_executes(monkeypatch):
    calls: list[str] = []

    @tool
    def fetch_fact() -> str:
        calls.append("run")
        return "tool says hi"

    class _AsyncModels:
        def __init__(self):
            self.calls = 0

        async def generate_content_stream(self, *, model, contents, config=None):
            self.calls += 1
            if self.calls == 1:
                return _FakeAsyncStream([_tool_call_chunk()])
            if self.calls == 2:
                return _FakeAsyncStream([_text_chunk("Summary: tool says hi")])
            raise AssertionError("unexpected extra async stream invocation")

    class _Client:
        def __init__(self):
            self.models = type(
                "_Sync",
                (),
                {
                    "generate_content_stream": lambda *_args, **_kwargs: _FakeStream(
                        [_text_chunk("noop")]
                    )
                },
            )()
            self.aio = type("_Aio", (), {"models": _AsyncModels()})()

    be = GeminiBackend()
    fake_client = _Client()
    be._client_sync = fake_client
    be._Types = _Types
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)

    cfg = Config(model="gemini-2.5-flash")
    aiter = await be.astream(
        "Use the fetch_fact tool to get info.",
        tools=[fetch_fact],
        output_schema=None,
        config=cfg,
    )

    chunks: list[str] = []
    async for chunk in aiter:
        chunks.append(chunk)

    assert "".join(chunks) == "Summary: tool says hi"
    assert calls == ["run"]
