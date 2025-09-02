from dataclasses import dataclass
import pytest
from alloy import ask, command, configure, CommandError
from alloy.config import Config
from alloy.models.base import ModelBackend

pytestmark = pytest.mark.unit


class FakeBackend(ModelBackend):
    def __init__(self):
        self.calls = 0

    def complete(self, prompt: str, *, tools=None, output_schema=None, config: Config) -> str:
        self.calls += 1
        if config.retry and self.calls < config.retry:
            raise CommandError("transient")
        if (
            output_schema
            and isinstance(output_schema, dict)
            and output_schema.get("type") == "object"
        ):
            return '{"value": 42, "label": "ok"}'
        return "12.5"

    def stream(self, prompt: str, *, tools=None, output_schema=None, config: Config):
        yield "hel"
        yield "lo"


def use_fake_backend(monkeypatch):
    import importlib

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: FakeBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: FakeBackend())


def test_command_sync_parsing_and_retry(monkeypatch):
    use_fake_backend(monkeypatch)
    configure(model="test-model", retry=2, retry_on=CommandError)

    @command(output=float)
    def extract_price(text: str) -> str:
        return f"extract price from: {text}"

    result = extract_price("$9.99")
    assert isinstance(result, float)
    assert result == 12.5


def test_command_structured_dataclass(monkeypatch):
    use_fake_backend(monkeypatch)
    configure(model="test-model")

    @dataclass
    class Out:
        value: int
        label: str

    @command(output=Out)
    def make() -> str:
        return "make output"

    out = make()
    assert isinstance(out, Out)
    assert out.value == 42
    assert out.label == "ok"


def test_streaming_sync(monkeypatch):
    use_fake_backend(monkeypatch)
    configure(model="test-model")

    @command(output=str)
    def generate() -> str:
        return "say hello"

    chunks = list(generate.stream())
    assert "".join(chunks) == "hello"


def test_ask_namespace(monkeypatch):
    use_fake_backend(monkeypatch)
    configure(model="test-model", retry=0, retry_on=None)
    assert callable(ask)
    assert hasattr(ask, "stream") and hasattr(ask, "stream_async")
    assert ask("hi") == "12.5"
    chunks = list(ask.stream("hi"))
    assert "".join(chunks) == "hello"
