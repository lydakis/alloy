from __future__ import annotations

import importlib
import pytest

from alloy import command, tool, configure
pytestmark = pytest.mark.providers


class _FakeAsyncResponses:
    def __init__(self) -> None:
        self.calls = 0
        self.history: list[dict] = []

    async def create(self, **kwargs):
        self.calls += 1
        self.history.append(kwargs)
        if self.calls == 1:
            # First turn: model asks to call two tools
            return {
                "id": "r1",
                "output": [
                    {"type": "function_call", "call_id": "c1", "name": "foo", "arguments": "{}"},
                    {"type": "function_call", "call_id": "c2", "name": "bar", "arguments": "{}"},
                ],
            }
        # Second turn: after tool outputs provided, model returns final output
        return {"id": "r2", "output_text": "ok"}


class _FakeAsyncOpenAI:
    last: "_FakeAsyncOpenAI | None" = None

    def __init__(self) -> None:
        self.responses = _FakeAsyncResponses()
        _FakeAsyncOpenAI.last = self


@tool
def foo() -> str:
    return "A"


@tool
def bar() -> str:
    return "B"


@pytest.mark.asyncio
async def test_openai_async_parallel_tools(monkeypatch):
    from alloy.models.openai import OpenAIBackend

    be = OpenAIBackend()
    be._AsyncOpenAI = _FakeAsyncOpenAI

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: be)
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: be)

    configure(model="gpt-5-mini")

    @command(output=str, tools=[foo, bar])
    async def hello() -> str:
        return "Use tools"

    out = await hello.async_()
    assert out.strip().lower() == "ok"

    fc = _FakeAsyncOpenAI.last
    assert fc is not None
    hist = fc.responses.history
    assert len(hist) == 2
    # Ensure we sent back two tool outputs in the same order as calls
    pending = hist[1]["input"]
    assert isinstance(pending, list)
    assert pending[0].get("call_id") == "c1"
    assert pending[1].get("call_id") == "c2"
