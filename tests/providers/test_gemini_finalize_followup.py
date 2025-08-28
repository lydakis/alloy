import pytest
from typing import Any

from alloy import tool
from alloy.config import Config


pytestmark = pytest.mark.providers


@tool
def foo() -> str:
    return "ok"


def test_gemini_finalize_followup_after_tools(monkeypatch):
    from alloy.models.gemini import GeminiBackend

    calls: list[tuple[str, dict]] = []

    class _RespCalls:
        text: str
        function_calls: list[Any]
        candidates: list[Any]
        parsed: dict[str, Any] | None

        def __init__(self, stage: int):
            self.text = ""
            self.function_calls = []
            self.candidates = []
            if stage == 1:

                class FC:
                    def __init__(self):
                        self.function_call = type("FCInner", (), {"name": "foo", "args": {}})()

                self.function_calls = [FC()]
            elif stage == 3:
                self.text = '{"x":"ok"}'
                self.parsed = {}

    class _FakeClient:
        class models:
            @staticmethod
            def generate_content(*, model, contents, config=None):
                # 1st: ask tool, 2nd: done w/o text, 3rd: finalize JSON
                idx = sum(1 for name, _ in calls if name == "generate") + 1
                calls.append(("generate", {"model": model, "config": config}))
                return _RespCalls(stage=idx)

    be = GeminiBackend()
    be._GenAIClient = lambda: _FakeClient()

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

    out = be.complete(
        "prompt",
        tools=[foo],
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        config=Config(model="gemini-1.5-pro"),
    )
    assert isinstance(out, str) and out.strip()
    assert len(calls) >= 3
    # Finalize (third) call config should not include tools/automatic_function_calling
    last_cfg = calls[-1][1]["config"] or {}
    assert "tools" not in last_cfg and "automatic_function_calling" not in last_cfg
