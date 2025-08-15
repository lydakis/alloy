import importlib.util
import pytest

from alloy.config import Config
from alloy import ConfigurationError
from alloy.models.base import get_backend


def test_routing_to_anthropic_backend():
    be = get_backend("claude-3.5-sonnet")
    # Avoid importing the class directly; just check class name to prevent coupling
    assert be.__class__.__name__ == "AnthropicBackend"


def test_anthropic_complete_requires_sdk():
    # If SDK is installed in this environment, skip this unit that expects missing SDK
    if importlib.util.find_spec("anthropic") is not None:
        pytest.skip("Anthropic SDK present; skipping missing-SDK unit")
    be = get_backend("claude-3.5-sonnet")
    with pytest.raises(ConfigurationError):
        be.complete("hi", config=Config(model="claude-3.5-sonnet"))


def test_routing_to_gemini_backend():
    be = get_backend("gemini-1.5-pro")
    assert be.__class__.__name__ == "GeminiBackend"


def test_routing_to_ollama_backend():
    be = get_backend("ollama:phi3")
    assert be.__class__.__name__ == "OllamaBackend"
