import pytest

from alloy import tool
from alloy.config import Config


pytestmark = pytest.mark.providers


@tool
def foo() -> str:
    return "ok"


def test_anthropic_finalize_followup_after_tools(monkeypatch):
    from alloy.models.anthropic import AnthropicBackend

    calls: list[dict] = []

    class _FakeMessages:
        def __init__(self, outer):
            self._outer = outer

        def create(self, **kwargs):
            calls.append(kwargs)
            idx = len(calls)
            if idx == 1:
                return type(
                    "Resp",
                    (),
                    {"content": [{"type": "tool_use", "id": "c1", "name": "foo", "input": {}}]},
                )()
            if idx == 2:
                return type("Resp", (), {"content": [{"type": "text", "text": ""}]})()
            return type("Resp", (), {"content": [{"type": "text", "text": '{"x":"ok"}'}]})()

    class _FakeClient:
        def __init__(self):
            self.messages = _FakeMessages(self)

    be = AnthropicBackend()
    be._Anthropic = lambda: _FakeClient()

    out = be.complete(
        "prompt",
        tools=[foo],
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        config=Config(model="claude-sonnet-4-20250514", auto_finalize_missing_output=True),
    )
    assert isinstance(out, str)
    assert len(calls) >= 2
    if len(calls) >= 3:
        last = calls[-1]
        assert "tools" not in last and "tool_choice" not in last
