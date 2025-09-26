import pytest

from alloy.models.anthropic import AnthropicBackend
from alloy.config import Config
from alloy import ConfigurationError, tool
from anthropic.types import Message


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
async def test_anthropic_astream_disallows_schema(monkeypatch):
    be = AnthropicBackend()
    be._client_async = _FakeAnthropicClient()
    monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)
    cfg = Config(model="claude-3")
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


def _make_message(content: list[dict[str, object]], *, stop_reason: str = "end_turn") -> Message:
    return Message.model_validate(
        {
            "id": "msg-test",
            "content": content,
            "model": "claude-3-sonnet",
            "role": "assistant",
            "stop_reason": stop_reason,
            "type": "message",
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
    )


class _SyncStream:
    def __init__(self, chunks: list[str], final_message: Message):
        self._chunks = chunks
        self._final = final_message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    @property
    def text_stream(self):
        def _gen():
            for chunk in self._chunks:
                yield chunk

        return _gen()

    def get_final_message(self) -> Message:
        return self._final


class _AsyncToolStream:
    def __init__(self, chunks: list[str], final_message: Message):
        self._chunks = chunks
        self._final = final_message

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    @property
    def text_stream(self):
        async def _gen():
            for chunk in self._chunks:
                yield chunk

        return _gen()

    async def get_final_message(self) -> Message:
        return self._final


def test_anthropic_stream_with_tools_executes_and_yields(monkeypatch):
    calls: list[str] = []

    @tool
    def fetch_fact() -> str:
        calls.append("run")
        return "tool says hi"

    tool_message = _make_message(
        [
            {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "fetch_fact",
                "input": {},
            }
        ],
        stop_reason="tool_use",
    )
    final_message = _make_message(
        [{"type": "text", "text": "Summary: tool says hi"}],
        stop_reason="end_turn",
    )

    class _SyncMessages:
        def __init__(self):
            self.calls = 0
            self.kwargs: list[dict[str, object]] = []

        def stream(self, **kwargs):
            self.kwargs.append(kwargs)
            self.calls += 1
            if self.calls == 1:
                return _SyncStream([], tool_message)
            if self.calls == 2:
                return _SyncStream(["Summary: tool says hi"], final_message)
            raise AssertionError("Unexpected additional stream invocation")

    class _SyncClient:
        def __init__(self):
            self.messages = _SyncMessages()

    be = AnthropicBackend()
    client = _SyncClient()
    be._client_sync = client
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)

    cfg = Config(model="claude-3")
    chunks = list(
        be.stream(
            "Use the fetch_fact tool to get info, then summarize.",
            tools=[fetch_fact],
            output_schema=None,
            config=cfg,
        )
    )

    assert "Summary: tool says hi" == "".join(chunks)
    assert calls == ["run"]
    # second turn should include tool_result payload in the request
    tool_turn = client.messages.kwargs[1]["messages"][-1]
    assert tool_turn["role"] == "user"
    assert tool_turn["content"][0]["type"] == "tool_result"


@pytest.mark.asyncio
async def test_anthropic_astream_with_tools_executes_and_yields(monkeypatch):
    calls: list[str] = []

    @tool
    def fetch_fact() -> str:
        calls.append("run")
        return "tool says hi"

    tool_message = _make_message(
        [
            {
                "type": "tool_use",
                "id": "toolu_2",
                "name": "fetch_fact",
                "input": {},
            }
        ],
        stop_reason="tool_use",
    )
    final_message = _make_message(
        [{"type": "text", "text": "Summary: tool says hi"}],
        stop_reason="end_turn",
    )

    class _AsyncMessages:
        def __init__(self):
            self.calls = 0
            self.kwargs: list[dict[str, object]] = []

        def stream(self, **kwargs):
            self.kwargs.append(kwargs)
            self.calls += 1
            if self.calls == 1:
                return _AsyncToolStream([], tool_message)
            if self.calls == 2:
                return _AsyncToolStream(["Summary: tool says hi"], final_message)
            raise AssertionError("Unexpected additional stream invocation")

    class _AsyncClient:
        def __init__(self):
            self.messages = _AsyncMessages()

    be = AnthropicBackend()
    client = _AsyncClient()
    be._client_async = client
    monkeypatch.setattr(be, "_get_async_client", lambda: be._client_async)

    cfg = Config(model="claude-3")
    aiter = await be.astream(
        "Use the fetch_fact tool to get info, then summarize.",
        tools=[fetch_fact],
        output_schema=None,
        config=cfg,
    )

    chunks: list[str] = []
    async for chunk in aiter:
        chunks.append(chunk)

    assert "".join(chunks) == "Summary: tool says hi"
    assert calls == ["run"]
    tool_turn = client.messages.kwargs[1]["messages"][-1]
    assert tool_turn["role"] == "user"
    assert tool_turn["content"][0]["type"] == "tool_result"
