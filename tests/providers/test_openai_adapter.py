import pytest
from unittest.mock import Mock

from alloy.config import Config


pytestmark = pytest.mark.providers


def test_openai_serializes_tools_and_schema(monkeypatch):
    from alloy.models.openai import OpenAIBackend
    from alloy.tool import tool

    calls: list[dict] = []

    class _FakeResponses:
        def create(self, **kwargs):
            calls.append(kwargs)
            # Return a simple text output to finish the loop
            return {"id": "r1", "output_text": "ok"}

        def stream(self, **kwargs):
            yield {"type": "response.output_text.delta", "delta": "ok"}

    class _FakeOpenAI:
        def __init__(self) -> None:
            self.responses = _FakeResponses()

    be = OpenAIBackend()
    be._OpenAI = _FakeOpenAI

    @tool
    def t() -> str:
        return "x"

    be.complete(
        "prompt",
        tools=[t],
        output_schema={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        config=Config(model="gpt-5-mini", temperature=0, max_tokens=64),
    )

    assert calls, "expected responses.create to be called"
    kwargs = calls[0]
    # Tools
    assert isinstance(kwargs.get("tools"), list) and kwargs["tools"][0]["type"] == "function"
    assert kwargs["tools"][0]["name"] == "t"
    # Schema is passed via text.format json_schema
    tf = (kwargs.get("text") or {}).get("format") or {}
    assert tf.get("type") == "json_schema"
    assert isinstance(tf.get("schema"), dict)
    # Model/temperature/tokens
    assert kwargs["model"] == "gpt-5-mini"
    assert kwargs.get("max_output_tokens") == 64


def test_openai_streaming_gating(monkeypatch):
    from alloy.models.openai import OpenAIBackend
    be = OpenAIBackend()
    be._OpenAI = lambda: Mock(responses=Mock(stream=lambda **k: []))

    with pytest.raises(Exception) as ei:
        list(
            be.stream(
                "prompt",
                tools=None,
                output_schema={"type": "number"},
                config=Config(model="gpt-5-mini"),
            )
        )
    assert "Streaming supports text only" in str(ei.value)
