import pytest

from alloy import tool, ToolLoopLimitExceeded
from alloy.config import Config


pytestmark = pytest.mark.providers


@tool
def foo() -> str:
    return "ok"


def test_anthropic_raises_on_tool_limit(monkeypatch):
    from alloy.models.anthropic import AnthropicBackend

    calls: list[dict] = []

    class _FakeMessages:
        def __init__(self, outer):
            self._outer = outer

        def create(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                return type(
                    "Resp",
                    (),
                    {"content": [{"type": "tool_use", "id": "c1", "name": "foo", "input": {}}]},
                )()
            return type(
                "Resp",
                (),
                {"content": [{"type": "tool_use", "id": "c2", "name": "foo", "input": {}}]},
            )()

    class _FakeClient:
        def __init__(self):
            self.messages = _FakeMessages(self)

    be = AnthropicBackend()
    be._Anthropic = lambda: _FakeClient()

    with pytest.raises(ToolLoopLimitExceeded):
        be.complete(
            "prompt",
            tools=[foo],
            output_schema={
                "type": "object",
                "properties": {"x": {"type": "string"}},
                "required": ["x"],
            },
            config=Config(model="claude-sonnet-4-20250514", max_tool_turns=0),
        )

    assert len(calls) == 1
