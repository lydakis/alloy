import pytest

from alloy.config import Config


pytestmark = pytest.mark.providers


def test_ollama_raises_on_tools(monkeypatch):
    from alloy.models.ollama import OllamaBackend
    from alloy import tool

    be = OllamaBackend()

    @tool
    def noop() -> str:
        return "ok"

    with pytest.raises(Exception):
        be.complete("prompt", tools=[noop], output_schema=None, config=Config(model="ollama:phi3"))


def test_ollama_stream_not_implemented():
    from alloy.models.ollama import OllamaBackend

    be = OllamaBackend()
    with pytest.raises(Exception):
        list(be.stream("p", tools=None, output_schema=None, config=Config(model="ollama:phi3")))
