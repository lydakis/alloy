import pytest

from alloy.config import Config

pytestmark = pytest.mark.providers


def test_anthropic_tool_params_optional_defaults(monkeypatch):
    from alloy.models.anthropic import AnthropicBackend
    from alloy import tool

    calls: list[dict] = []

    class _Resp:
        def __init__(self):
            self.content = [{"type": "text", "text": "ok"}]

    class _Client:
        class messages:
            pass

        def __init__(self):
            self.calls = calls

        def messages_create(self, **kwargs):
            self.calls.append(kwargs)
            return _Resp()

    be = AnthropicBackend()
    client = _Client()
    be._client_sync = type(
        "C", (), {"messages": type("M", (), {"create": client.messages_create})()}
    )()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    be.complete(
        "prompt",
        tools=[add],
        output_schema=None,
        config=Config(model="claude-3"),
    )

    assert calls, "expected messages.create to be called"
    kwargs = calls[0]
    tools = kwargs.get("tools") or []
    assert tools and isinstance(tools[0], dict)
    schema = tools[0].get("input_schema") or {}
    assert schema.get("type") == "object"
    assert schema.get("required") == ["a"]
    props = schema.get("properties") or {}
    assert "a" in props and "b" in props
