import pytest

from alloy.config import Config


pytestmark = pytest.mark.providers


def test_gemini_tool_params_optional_defaults(monkeypatch):
    from alloy.models.gemini import GeminiBackend
    from alloy import tool

    calls: list[tuple[str, dict]] = []

    class _FakeClient:
        class models:
            @staticmethod
            def generate_content(*, model, contents, config=None):
                calls.append(("generate_content_sync", {"model": model, "config": config}))

                class _Resp:
                    text = "ok"

                return _Resp()

        class aio:
            class models:
                @staticmethod
                async def generate_content(*, model, contents, config=None):
                    class _Resp:
                        text = "ok"

                    return _Resp()

    be = GeminiBackend()
    be._GenAIClient = lambda: _FakeClient()

    class _Types:
        class Schema:
            def __init__(self, **kwargs):
                self.kw = kwargs

        class FunctionDeclaration:
            def __init__(self, **kwargs):
                self.kw = kwargs

        class Tool:
            def __init__(self, **kwargs):
                self.kw = kwargs

        class AutomaticFunctionCallingConfig:
            def __init__(self, **kwargs):
                self.kw = kwargs

        class Content:
            def __init__(self, **kwargs):
                self.kw = kwargs

        class Part:
            @staticmethod
            def from_text(text: str):
                return text

    be._Types = _Types

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    be.complete(
        "prompt",
        tools=[add],
        output_schema=None,
        config=Config(model="gemini-2.5-flash", temperature=0, max_tokens=64),
    )

    assert calls, "expected a generate_content call"
    _name, payload = calls[0]
    cfg = payload.get("config") or {}
    tools_wrapped = cfg.get("tools") or []
    assert tools_wrapped, "expected tool declarations present in config"
    tool_obj = tools_wrapped[0]
    decls = tool_obj.kw.get("function_declarations") or []
    assert decls and hasattr(decls[0], "kw")
    params = decls[0].kw.get("parameters")
    assert isinstance(params, _Types.Schema)
    assert params.kw.get("type") == "OBJECT"
    assert params.kw.get("required") == ["a"]
