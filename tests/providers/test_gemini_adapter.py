import pytest

from alloy.config import Config


pytestmark = pytest.mark.providers


def test_gemini_serializes_schema_without_tools(monkeypatch):
    from alloy.models.gemini import GeminiBackend

    # capture last call
    calls: list[tuple[str, dict]] = []

    class _FakeAio:
        class models:
            @staticmethod
            async def generate_content(*, model, contents, config=None):
                calls.append(("generate_content", {"model": model, "config": config}))

                class _Resp:
                    text = "ok"

                return _Resp()

    class _FakeClient:
        def __init__(self) -> None:
            self.aio = _FakeAio()

        class models:
            @staticmethod
            def generate_content(*, model, contents, config=None):
                calls.append(("generate_content_sync", {"model": model, "config": config}))

                class _Resp:
                    text = "ok"

                return _Resp()

    be = GeminiBackend()
    be._GenAIClient = lambda: _FakeClient()

    # Minimal stub types used by backend for config/schema building
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

    be.complete(
        "prompt",
        tools=None,
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        config=Config(
            model="gemini-2.5-flash", temperature=0, max_tokens=128, default_system="sys"
        ),
    )

    assert calls, "expected a generate_content call"
    _name, payload = calls[0]
    cfg = payload["config"] or {}
    assert cfg.get("response_mime_type") == "application/json"
    assert isinstance(cfg.get("response_json_schema"), _Types.Schema) or cfg.get(
        "response_json_schema"
    )


def test_gemini_omits_schema_when_tools_present(monkeypatch):
    from alloy.models.gemini import GeminiBackend

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

    from alloy import tool

    @tool
    def t() -> str:
        return "ok"

    be.complete(
        "prompt",
        tools=[t],
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        config=Config(
            model="gemini-2.5-flash", temperature=0, max_tokens=128, default_system="sys"
        ),
    )

    assert calls, "expected a generate_content call"
    _name, payload = calls[0]
    cfg = payload["config"] or {}
    assert cfg.get("response_mime_type") is None
    assert cfg.get("response_json_schema") is None
