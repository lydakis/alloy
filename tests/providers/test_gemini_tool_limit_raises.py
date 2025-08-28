import pytest
from typing import Any

from alloy import tool, ToolLoopLimitExceeded
from alloy.config import Config


pytestmark = pytest.mark.providers


@tool
def foo() -> str:
    return "ok"


def test_gemini_raises_on_tool_limit(monkeypatch):
    from alloy.models.gemini import GeminiBackend

    calls: list[tuple[str, dict]] = []

    class _RespCalls:
        text: str
        function_calls: list[Any]
        candidates: list[Any]
        def __init__(self, with_call: bool):
            if with_call:
                class FC:
                    def __init__(self):
                        self.function_call = type("FCInner", (), {"name": "foo", "args": {}})()

                self.function_calls = [FC()]
                self.candidates = []
            else:
                self.function_calls = []
                self.candidates = []
            self.text = ""

    class _FakeClient:
        class models:
            @staticmethod
            def generate_content(*, model, contents, config=None):
                # 1st call: asks for tool; 2nd call: asks again -> exceeds
                idx = sum(1 for name, _ in calls if name == "generate") + 1
                calls.append(("generate", {"model": model, "config": config}))
                return _RespCalls(with_call=True if idx <= 2 else False)

    be = GeminiBackend()
    be._GenAIClient = lambda: _FakeClient()
    # Minimal types for the adapter
    class _Types:
        class Schema:
            def __init__(self, **kwargs):
                pass
        class FunctionDeclaration:
            def __init__(self, **kwargs):
                pass
        class Tool:
            def __init__(self, **kwargs):
                pass
        class AutomaticFunctionCallingConfig:
            def __init__(self, **kwargs):
                pass
        class Content:
            def __init__(self, **kwargs):
                pass
        class Part:
            @staticmethod
            def from_text(text: str):
                return text
            @staticmethod
            def from_function_response(name: str, response):
                return {"name": name, "response": response}

    be._Types = _Types

    with pytest.raises(ToolLoopLimitExceeded):
        be.complete(
            "prompt",
            tools=[foo],
            output_schema={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
            config=Config(model="gemini-1.5-pro", max_tool_turns=1),
        )

    # Only two calls (no finalize)
    gen_calls = [c for c in calls if c[0] == "generate"]
    assert len(gen_calls) == 2
