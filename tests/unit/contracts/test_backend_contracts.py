import inspect
import pytest

from alloy.models.base import ModelBackend
from alloy.models.openai import OpenAIBackend
from alloy.models.anthropic import AnthropicBackend
from alloy.models.gemini import GeminiBackend
from alloy.models.ollama import OllamaBackend


@pytest.mark.parametrize(
    "backend_cls",
    [OpenAIBackend, AnthropicBackend, GeminiBackend, OllamaBackend],
)
def test_backend_interface_methods_present(backend_cls):
    be: ModelBackend = backend_cls()
    assert hasattr(be, "complete")
    assert hasattr(be, "stream")
    assert hasattr(be, "acomplete")
    assert hasattr(be, "astream")
    assert callable(getattr(be, "complete"))
    assert callable(getattr(be, "stream"))
    assert callable(getattr(be, "acomplete"))
    assert callable(getattr(be, "astream"))


@pytest.mark.parametrize(
    "backend_cls",
    [OpenAIBackend, AnthropicBackend, GeminiBackend, OllamaBackend],
)
def test_backend_astream_is_coroutine(backend_cls):
    be: ModelBackend = backend_cls()
    astream = getattr(be, "astream")
    assert inspect.iscoroutinefunction(astream)
