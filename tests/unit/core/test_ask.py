import importlib
import pytest

from alloy import ask, CommandError

pytestmark = pytest.mark.unit


def test_ask_adds_context_and_calls_backend(monkeypatch):
    class _FakeBackend:
        def __init__(self):
            self.last_prompt = None

        def complete(self, prompt: str, *, tools=None, output_schema=None, config=None) -> str:
            self.last_prompt = prompt
            return prompt

    fb = _FakeBackend()
    mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(mod, "get_backend", lambda model: fb)
    monkeypatch.setenv("ALLOY_MODEL", "gpt-5-mini")
    out = ask("Do it", context={"k": 1})
    assert "Context:" in out and "Task:" in out
    assert fb.last_prompt == out


def test_ask_stream_rejects_tools(monkeypatch):
    with pytest.raises(CommandError):
        list(ask.stream("hello", tools=[lambda: None]))


@pytest.mark.asyncio
async def test_ask_stream_async_happy_path(monkeypatch):
    class _FakeBackend:
        async def astream(self, prompt: str, *, tools=None, output_schema=None, config=None):
            async def agen():
                yield "ok"

            return agen()

    mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(mod, "get_backend", lambda model: _FakeBackend())
    monkeypatch.setenv("ALLOY_MODEL", "gpt-5-mini")

    out = []
    aiter = ask.stream_async("Say OK")
    async for ch in aiter:
        out.append(ch)
        break
    await aiter.aclose()
    assert "".join(out) == "ok"


@pytest.mark.asyncio
async def test_ask_stream_async_includes_context_in_prompt(monkeypatch):
    captured: dict[str, str] = {}

    class _AsyncBackend:
        async def astream(self, prompt: str, *, tools=None, output_schema=None, config=None):
            captured["prompt"] = prompt

            async def agen():
                if False:
                    yield "unused"

            return agen()

    ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(ask_mod, "get_backend", lambda model: _AsyncBackend())
    monkeypatch.setenv("ALLOY_MODEL", "gpt-5-mini")

    aiter = ask.stream_async("run", context={"user": 1}, model="gpt-5-mini")
    async for _ in aiter:
        pass
    await aiter.aclose()
    prompt = captured.get("prompt", "")
    assert "Context:" in prompt and "Task:" in prompt
