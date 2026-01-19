import pytest

from alloy.config import Config

pytestmark = pytest.mark.providers


def test_openai_tool_params_optional_defaults(monkeypatch):
    from alloy.models.openai import OpenAIBackend
    from alloy import tool

    calls: list[dict] = []

    class _FakeResponses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return {"id": "r1", "output_text": "ok"}

        def stream(self, **kwargs):
            yield {"type": "response.output_text.delta", "delta": "ok"}

    class _FakeOpenAI:
        def __init__(self) -> None:
            self.responses = _FakeResponses()

    be = OpenAIBackend()
    be._OpenAI = _FakeOpenAI

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    be.complete(
        "prompt",
        tools=[add],
        output_schema=None,
        config=Config(model="gpt-5-mini", temperature=0, max_tokens=64),
    )

    assert calls, "expected responses.create to be called"
    kwargs = calls[0]
    tools = kwargs.get("tools") or []
    assert tools and isinstance(tools[0], dict)
    params = tools[0].get("parameters") or {}
    assert params.get("type") == "object"
    assert params.get("required") == ["a"]
    props = params.get("properties") or {}
    assert "a" in props and "b" in props
