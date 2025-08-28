import pytest
from alloy import ask, command, ConfigurationError, CommandError, tool

pytestmark = pytest.mark.unit


def test_command_stream_disallowed_with_typed_output():
    @command(output=int)
    def compute() -> str:
        return "Compute 2+2"

    with pytest.raises(ConfigurationError) as ei:
        _ = list(compute.stream())
    assert "Streaming supports text-only commands" in str(ei.value)


def test_command_stream_disallowed_with_tools():
    @tool
    def t1() -> str:
        return "ok"

    @command(output=str, tools=[t1])
    def with_tools() -> str:
        return "Say hi"

    with pytest.raises(ConfigurationError) as ei:
        _ = list(with_tools.stream())
    assert "Streaming supports text-only commands" in str(ei.value)


def test_ask_stream_allows_plain_text(fake_backend):
    # Script a few chunks
    fake_backend.next.extend(
        [
            {"type": "text_chunk", "data": "hel"},
            {"type": "text_chunk", "data": "lo"},
        ]
    )

    chunks = list(ask.stream("Say hello"))
    assert "".join(chunks) == "hello"


def test_ask_stream_disallowed_with_tools():
    @tool
    def noop() -> str:
        return "ok"

    with pytest.raises(CommandError) as ei:
        _ = list(ask.stream("Say hi", tools=[noop]))
    assert "Streaming supports text only; tools are not supported" in str(ei.value)
