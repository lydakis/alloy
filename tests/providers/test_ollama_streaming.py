import pytest

from alloy.models.ollama import OllamaBackend
from alloy.config import Config
from alloy import ConfigurationError


@pytest.mark.asyncio
async def test_ollama_astream_not_implemented():
    be = OllamaBackend()
    cfg = Config(model="ollama:phi3")
    with pytest.raises(ConfigurationError):
        await be.astream("prompt", tools=None, output_schema=None, config=cfg)
