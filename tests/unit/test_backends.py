import importlib.util
import pytest
from alloy.config import Config
from alloy import ConfigurationError
from alloy.models.base import get_backend

pytestmark = pytest.mark.unit


def test_routing_to_anthropic_backend():
    be = get_backend("claude-sonnet-4-20250514")
    assert be.__class__.__name__ == "AnthropicBackend"


def test_anthropic_complete_requires_sdk():
    if importlib.util.find_spec("anthropic") is not None:
        pytest.skip("Anthropic SDK present; skipping missing-SDK unit")
    be = get_backend("claude-sonnet-4-20250514")
    with pytest.raises(ConfigurationError):
        be.complete("hi", config=Config(model="claude-sonnet-4-20250514"))


def test_routing_to_gemini_backend():
    be = get_backend("gemini-2.5-flash")
    assert be.__class__.__name__ == "GeminiBackend"


def test_routing_to_ollama_backend():
    be = get_backend("ollama:gpt-oss")
    assert be.__class__.__name__ == "OllamaBackend"


def test_gemini_complete_requires_sdk():
    if importlib.util.find_spec("google.genai") is not None:
        pytest.skip("Gemini SDK present; skipping missing-SDK unit")
    be = get_backend("gemini-2.5-flash")
    with pytest.raises(ConfigurationError):
        be.complete("hi", config=Config(model="gemini-2.5-flash"))


def test_ollama_complete_requires_sdk():
    if importlib.util.find_spec("ollama") is not None:
        pytest.skip("Ollama SDK present; skipping missing-SDK unit")
    be = get_backend("ollama:phi3")
    with pytest.raises(ConfigurationError):
        be.complete("hi", config=Config(model="ollama:phi3"))
