import pytest
from alloy import ask, command, ConfigurationError, CommandError, tool

pytestmark = pytest.mark.unit


def test_command_stream_disallowed_with_typed_output():
    @command(output=int)
    def compute() -> str:
        return "Compute 2+2"

    with pytest.raises(ConfigurationError) as ei:
        _ = list(compute.stream())
    assert "non-string typed outputs" in str(ei.value)


def test_command_stream_disallowed_with_tools(monkeypatch):
    monkeypatch.setenv("ALLOY_BACKEND", "fake")

    @tool
    def t1() -> str:
        return "ok"

    @command(output=str, tools=[t1])
    def with_tools() -> str:
        return "Say hi"

    with pytest.raises(ConfigurationError) as ei:
        _ = list(with_tools.stream())
    assert "Streaming with tools" in str(ei.value)


def test_ask_stream_allows_plain_text(fake_backend):
    fake_backend.next.extend(
        [
            {"type": "text_chunk", "data": "hel"},
            {"type": "text_chunk", "data": "lo"},
        ]
    )

    chunks = list(ask.stream("Say hello"))
    assert "".join(chunks) == "hello"


def test_ask_stream_disallowed_with_tools(monkeypatch):
    monkeypatch.setenv("ALLOY_BACKEND", "fake")

    @tool
    def noop() -> str:
        return "ok"

    with pytest.raises(CommandError) as ei:
        _ = list(ask.stream("Say hi", tools=[noop]))
    assert "Streaming with tools" in str(ei.value)


def test_command_stream_allows_tools_when_backend_supports(monkeypatch):
    from alloy.models.base import ModelBackend

    captured = {}

    class FakeBackend(ModelBackend):
        supports_streaming_tools = True

        def complete(self, *args, **kwargs):
            raise NotImplementedError

        def stream(self, prompt, *, tools=None, output_schema=None, config):
            captured["tools"] = tools

            def gen():
                yield "chunk"

            return gen()

        async def acomplete(self, *args, **kwargs):
            raise NotImplementedError

        async def astream(self, *args, **kwargs):
            raise NotImplementedError

    import importlib

    command_module = importlib.import_module("alloy.command")

    backend = FakeBackend()
    monkeypatch.setattr(command_module, "get_backend", lambda model: backend)

    @tool
    def helper() -> str:
        return "ok"

    @command(output=str, tools=[helper])
    def with_tools() -> str:
        return "Say hi"

    chunks = list(with_tools.stream())
    assert "".join(chunks) == "chunk"
    assert captured["tools"] is not None
    assert len(captured["tools"]) == 1


def test_ask_stream_allows_tools_when_backend_supports(monkeypatch):
    from alloy.models.base import ModelBackend

    class FakeBackend(ModelBackend):
        supports_streaming_tools = True

        def complete(self, *args, **kwargs):
            raise NotImplementedError

        def stream(self, prompt, *, tools=None, output_schema=None, config):
            assert tools is not None and len(tools) == 1

            def gen():
                yield "hi"

            return gen()

        async def acomplete(self, *args, **kwargs):
            raise NotImplementedError

        async def astream(self, *args, **kwargs):
            raise NotImplementedError

    import importlib

    ask_module = importlib.import_module("alloy.ask")

    backend = FakeBackend()
    monkeypatch.setattr(ask_module, "get_backend", lambda model: backend)

    @tool
    def noop() -> str:
        return "ok"

    chunks = list(ask.stream("hi", tools=[noop]))
    assert chunks == ["hi"]
