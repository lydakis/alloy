import pytest

from alloy.config import Config
from alloy.tool import tool


pytestmark = pytest.mark.providers


def test_anthropic_serializes_tools_and_system(monkeypatch):
    from alloy.models.anthropic import AnthropicBackend

    calls: list[dict] = []

    class _FakeClient:
        class messages:
            @staticmethod
            def create(**kwargs):
                calls.append(kwargs)
                # mimic a minimal Claude response with text content
                return {"content": [{"type": "text", "text": "ok"}]}

    be = AnthropicBackend()
    be._Anthropic = lambda: _FakeClient()

    @tool
    def foo(x: int) -> int:
        return x * 2

    be.complete(
        "prompt",
        tools=[foo],
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        config=Config(model="claude-3-5-sonnet-latest", temperature=0.1, max_tokens=256, default_system="sys"),
    )

    assert calls, "expected messages.create to be called"
    kw = calls[0]
    assert kw["model"].startswith("claude")
    assert isinstance(kw.get("max_tokens"), int) and kw["max_tokens"] > 0
    # System includes provided system string plus any hint when structured outputs are present
    assert isinstance(kw.get("system"), str)
    # Tools are serialized into messages.create tools field
    tools = kw.get("tools")
    assert isinstance(tools, list) and tools and tools[0].get("name") == "foo"

