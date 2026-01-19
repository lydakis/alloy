import pytest
from typing import Any

from alloy.config import Config
from alloy.models.anthropic import AnthropicBackend

pytestmark = pytest.mark.providers


def test_anthropic_finalize_followup_removes_tools_and_adds_strict(monkeypatch):
    calls: list[dict[str, Any]] = []

    class _FakeMessages:
        def __init__(self) -> None:
            self._count = 0

        def create(self, **kwargs: Any) -> Any:
            calls.append(kwargs)
            self._count += 1
            if self._count == 1:
                return {"content": [{"type": "text", "text": ""}]}
            return {"content": [{"type": "text", "text": '{"x":"ok"}'}]}

    class _FakeClient:
        def __init__(self) -> None:
            self.messages = _FakeMessages()

    be = AnthropicBackend()
    be._Anthropic = lambda: _FakeClient()

    out = be.complete(
        "prompt",
        tools=[],
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
            "additionalProperties": False,
        },
        config=Config(model="claude-sonnet-4-20250514", auto_finalize_missing_output=True),
    )

    assert isinstance(out, str) and out.strip()
    assert len(calls) == 2
    final_kwargs = calls[1]
    assert "tools" not in final_kwargs
    assert "tool_choice" not in final_kwargs
    msgs = final_kwargs.get("messages", [])
    assert any(
        isinstance(b.get("content"), list)
        and any(
            (c.get("type") == "text" and "json object" in c.get("text", "").lower())
            for c in b.get("content", [])
        )
        for b in msgs
        if isinstance(b, dict)
    )
