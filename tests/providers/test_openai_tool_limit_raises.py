from __future__ import annotations

import importlib
import pytest

from alloy import command, tool, configure, ToolLoopLimitExceeded

pytestmark = pytest.mark.providers


class _FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.count = 0

    def create(self, **kwargs):
        self.calls.append(kwargs)
        self.count += 1
        if self.count == 1:
            return {
                "id": "r1",
                "output": [
                    {
                        "type": "function_call",
                        "call_id": "c1",
                        "name": "dummy",
                        "arguments": "{}",
                    }
                ],
            }
        return {
            "id": "r2",
            "output": [
                {
                    "type": "function_call",
                    "call_id": "c2",
                    "name": "dummy",
                    "arguments": "{}",
                }
            ],
        }


class _FakeOpenAI:
    last: "_FakeOpenAI | None" = None

    def __init__(self) -> None:
        self.responses = _FakeResponses()
        _FakeOpenAI.last = self


@tool
def dummy() -> str:
    return "ok"


def test_openai_raises_on_tool_limit(monkeypatch):
    from alloy.models.openai import OpenAIBackend

    be = OpenAIBackend()
    be._OpenAI = _FakeOpenAI

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: be)
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: be)

    configure(model="gpt-5-mini", max_tool_turns=1)

    @command(output=str, tools=[dummy])
    def hello() -> str:
        return "Say OK"

    with pytest.raises(ToolLoopLimitExceeded) as ei:
        hello()
    msg = str(ei.value)
    assert "max_tool_turns=1" in msg
    assert "turns_taken=" in msg

    fc = _FakeOpenAI.last
    assert fc is not None
    assert len(fc.responses.calls) == 2
