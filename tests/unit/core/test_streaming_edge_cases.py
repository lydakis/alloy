import pytest

from alloy import ask, command


pytestmark = pytest.mark.unit


def test_empty_stream_returns_no_chunks(fake_backend):
    chunks_ask = list(ask.stream("hello", model="gpt-5-mini"))
    assert chunks_ask == []

    @command(output=str)
    def generate() -> str:
        return "say hi"

    chunks_cmd = list(generate.stream())
    assert chunks_cmd == []


def test_stream_raises_midway_propagates_error(fake_backend, monkeypatch):
    def broken_stream(prompt: str, *, tools=None, output_schema=None, config=None):
        def gen():
            yield "start"
            raise RuntimeError("Network error")

        return gen()

    monkeypatch.setattr(fake_backend, "stream", broken_stream)

    it = ask.stream("stream please", model="gpt-5-mini")
    assert next(it) == "start"
    with pytest.raises(RuntimeError):
        next(it)
