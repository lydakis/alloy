import pytest

from alloy.config import Config


pytestmark = pytest.mark.providers


def test_ollama_accepts_tools_native(monkeypatch):
    from alloy.models.ollama import OllamaBackend
    from alloy import tool

    calls: list[dict] = []

    class _FakeClient:
        def chat(self, **kwargs):
            calls.append(kwargs)
            return {"message": {"role": "assistant", "content": "ok"}, "done": True}

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_client", lambda: _FakeClient())

    @tool
    def noop() -> str:
        return "ok"

    out = be.complete(
        "prompt",
        tools=[noop],
        output_schema=None,
        config=Config(model="ollama:llama3"),
    )
    assert out.strip() == "ok"
    assert calls and isinstance(calls[0].get("tools"), list)


def test_ollama_stream_text_native(monkeypatch):
    from alloy.models.ollama import OllamaBackend

    class _Chunk:
        def __init__(self, text: str) -> None:
            self.message = type("Msg", (), {"content": text})

    class _FakeClient:
        def chat(self, **kwargs):
            return [_Chunk("Hello"), _Chunk(" world")]

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_client", lambda: _FakeClient())
    out = "".join(
        be.stream("p", tools=None, output_schema=None, config=Config(model="ollama:llama3"))
    )
    assert out == "Hello world"


def test_ollama_serializes_tools_and_calls(monkeypatch):
    from alloy.models.ollama import OllamaBackend
    from alloy import tool

    calls: list[dict] = []

    class _FakeClient:
        def __init__(self) -> None:
            self.count = 0

        def chat(self, **kwargs):
            calls.append(kwargs)
            self.count += 1
            if self.count == 1:
                return {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{"function": {"name": "add", "arguments": {"a": 2}}}],
                    },
                    "done": True,
                }
            return {"message": {"role": "assistant", "content": "3"}, "done": True}

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_client", lambda: _FakeClient())

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    out = be.complete(
        "Use add(a=2) and return result.",
        tools=[add],
        output_schema=None,
        config=Config(model="ollama:llama3"),
    )
    assert out.strip() == "3"
    assert calls, "expected chat to be called"
    first = calls[0]
    assert isinstance(first.get("tools"), list)
    assert "format" not in first


def test_ollama_finalize_followup(monkeypatch):
    from alloy.models.ollama import OllamaBackend

    calls: list[dict] = []

    class _FakeClient:
        def __init__(self) -> None:
            self.count = 0

        def chat(self, **kwargs):
            calls.append(kwargs)
            self.count += 1
            if self.count == 1:
                return {"message": {"role": "assistant", "content": ""}, "done": True}
            return {
                "message": {
                    "role": "assistant",
                    "content": '{"x":"ok"}',
                },
                "done": True,
            }

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_client", lambda: _FakeClient())

    out = be.complete(
        "Return an object with x='ok'",
        tools=None,
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        config=Config(model="ollama:llama3", auto_finalize_missing_output=True),
    )
    assert out.strip()
    assert len(calls) >= 2
    finalize_kwargs = calls[-1]
    assert "format" in finalize_kwargs and "tools" not in finalize_kwargs


def test_ollama_tool_limit_raises(monkeypatch):
    import importlib
    from alloy.models.ollama import OllamaBackend
    from alloy import tool, ToolLoopLimitExceeded

    class _FakeClient:
        def __init__(self) -> None:
            self.count = 0

        def chat(self, **kwargs):
            self.count += 1
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": "noop", "arguments": {}}}],
                },
                "done": True,
            }

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_client", lambda: _FakeClient())

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: be)
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: be)

    @tool
    def noop() -> str:
        return "ok"

    from alloy import command, configure

    configure(model="ollama:llama3", max_tool_turns=1)

    @command(output=str, tools=[noop])
    def hello() -> str:
        return "Say hi"

    with pytest.raises(ToolLoopLimitExceeded):
        hello()


def test_ollama_openai_chat_tool_flow(monkeypatch):
    from alloy.models.ollama import OllamaBackend
    from alloy import tool

    calls: list[dict] = []

    class _Msg:
        def __init__(self, content: str, tool_calls: list | None = None):
            self.content = content
            self.tool_calls = tool_calls or []

    class _TCFunc:
        def __init__(self, name: str, arguments: str):
            self.name = name
            self.arguments = arguments

    class _TCall:
        def __init__(self, name: str, arguments: str, id_: str = "tc_1"):
            self.id = id_
            self.type = "function"
            self.function = _TCFunc(name, arguments)

    class _Choice:
        def __init__(self, message: _Msg):
            self.message = message

    class _Resp:
        def __init__(self, msg: _Msg):
            self.choices = [_Choice(msg)]

    class _FakeOpenAI:
        def __init__(self) -> None:
            self.count = 0

            class _Completions:
                def __init__(self, outer) -> None:
                    self._outer = outer

                def create(self, **kwargs):
                    calls.append(kwargs)
                    self._outer.count += 1
                    if self._outer.count == 1:
                        tc = _TCall("add", '{"a":2}')
                        return _Resp(_Msg("", [tc]))
                    return _Resp(_Msg("3"))

            class _Chat:
                def __init__(self, outer) -> None:
                    self.completions = _Completions(outer)

            self.chat = _Chat(self)

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_openai_client", lambda: _FakeOpenAI())

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    out = be.complete(
        "Use add(a=2) and return result.",
        tools=[add],
        output_schema=None,
        config=Config(model="ollama:llama3", extra={"ollama_api": "openai_chat"}),
    )
    assert out.strip() == "3"
    assert calls and isinstance(calls[0].get("tools"), list)


def test_ollama_openai_stream_text(monkeypatch):
    from alloy.models.ollama import OllamaBackend

    class _Delta:
        def __init__(self, content: str) -> None:
            self.content = content

    class _EventChoice:
        def __init__(self, delta: _Delta) -> None:
            self.delta = delta

    class _Event:
        def __init__(self, text: str) -> None:
            self.choices = [_EventChoice(_Delta(text))]

    class _FakeOpenAI:
        class _Completions:
            def create(self, **kwargs):
                return iter([_Event("Hello"), _Event(" world")])

        class _Chat:
            def __init__(self) -> None:
                self.completions = _FakeOpenAI._Completions()

        def __init__(self) -> None:
            self.chat = _FakeOpenAI._Chat()

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_openai_client", lambda: _FakeOpenAI())

    chunks = list(
        be.stream(
            "p",
            tools=None,
            output_schema=None,
            config=Config(model="ollama:llama3", extra={"ollama_api": "openai_chat"}),
        )
    )
    assert "".join(chunks) == "Hello world"


def test_ollama_openai_finalize_followup(monkeypatch):
    from alloy.models.ollama import OllamaBackend

    calls: list[dict] = []

    class _Msg:
        def __init__(self, content: str):
            self.content = content
            self.tool_calls: list[object] = []

    class _Choice:
        def __init__(self, message: _Msg):
            self.message = message

    class _Resp:
        def __init__(self, msg: _Msg):
            self.choices = [_Choice(msg)]

    class _FakeOpenAI:
        def __init__(self) -> None:
            self.count = 0

            class _Completions:
                def __init__(self, outer) -> None:
                    self._outer = outer

                def create(self, **kwargs):
                    calls.append(kwargs)
                    self._outer.count += 1
                    if self._outer.count == 1:
                        return _Resp(_Msg(""))
                    return _Resp(_Msg('{"x":"ok"}'))

            class _Chat:
                def __init__(self, outer) -> None:
                    self.completions = _Completions(outer)

            self.chat = _Chat(self)

    be = OllamaBackend()
    monkeypatch.setattr(be, "_get_openai_client", lambda: _FakeOpenAI())

    out = be.complete(
        "Return an object with x='ok'",
        tools=None,
        output_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        config=Config(
            model="ollama:llama3",
            auto_finalize_missing_output=True,
            extra={"ollama_api": "openai_chat"},
        ),
    )
    assert out.strip() == '{"x":"ok"}'
    assert len(calls) >= 2
