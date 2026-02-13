import pytest

from alloy.models.ollama import OllamaBackend
from alloy.config import Config
from alloy import ConfigurationError


@pytest.mark.asyncio
async def test_ollama_astream_disallows_tools_and_typed_outputs():
    be = OllamaBackend()
    cfg = Config(model="ollama:gpt-oss")
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=[lambda: None], output_schema=None, config=cfg)
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=None, output_schema={"type": "string"}, config=cfg)


def test_ollama_stream_disallows_tools_and_typed_outputs():
    be = OllamaBackend()
    cfg = Config(model="ollama:gpt-oss")
    with pytest.raises(ConfigurationError):
        list(be.stream("prompt", tools=[lambda: None], output_schema=None, config=cfg))
    with pytest.raises(ConfigurationError):
        list(be.stream("prompt", tools=None, output_schema={"type": "string"}, config=cfg))
