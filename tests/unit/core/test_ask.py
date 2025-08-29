import importlib
import pytest

from alloy import ask, CommandError


pytestmark = pytest.mark.unit


def test_ask_includes_context_in_prompt(monkeypatch):
    captured = {}

    class _CapBackend:
        def complete(self, prompt: str, *, tools=None, output_schema=None, config=None) -> str:
            captured["prompt"] = prompt
            return "ok"

        def stream(self, *a, **k):
            return iter(["x"])

    ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(ask_mod, "get_backend", lambda model: _CapBackend())
    out = ask("Run", context={"k": 1}, model="gpt-5-mini")
    assert out == "ok"
    assert "Context:" in captured.get("prompt", "") and "Task:" in captured.get("prompt", "")


def test_ask_wraps_backend_exception(monkeypatch):
    class _FailBackend:
        def complete(self, *a, **k) -> str:
            raise RuntimeError("boom")

    ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(ask_mod, "get_backend", lambda model: _FailBackend())
    with pytest.raises(CommandError):
        ask("hi", model="gpt-5-mini")


@pytest.mark.asyncio
async def test_ask_stream_async_disallowed_with_tools():
    with pytest.raises(CommandError):
        await ask.stream_async("hi", tools=[lambda: None], model="gpt-5-mini")

