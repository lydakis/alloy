from __future__ import annotations

import types
from types import SimpleNamespace as NS

from alloy.models.openai import OpenAIBackend
from alloy.config import Config
from alloy import tool, require


def test_openai_backend_surfaces_toolerror_message(monkeypatch):
    calls: list[dict] = []

    class FakeChatCompletions:
        def __init__(self):
            self.count = 0

        def create(self, **kwargs):
            calls.append(kwargs)
            self.count += 1
            if self.count == 1:
                # First call: request a tool call
                tc = NS(function=NS(name="always_fail", arguments="{}"), id="tc1")
                msg = NS(content="", tool_calls=[tc])
                return NS(choices=[NS(message=msg)])
            else:
                # Second call: final assistant content
                msg = NS(content="OK", tool_calls=None)
                return NS(choices=[NS(message=msg)])

    class FakeOpenAI:
        def __init__(self):
            self.chat = NS(completions=FakeChatCompletions())

    fake_mod = types.ModuleType("openai")
    fake_mod.OpenAI = FakeOpenAI
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_mod)

    @tool
    @require(lambda ba: False, "please validate first")
    def always_fail() -> str:  # no args needed for test
        return "never called"

    backend = OpenAIBackend()
    out = backend.complete(
        "Do the thing",
        tools=[always_fail],
        output_schema=None,
        config=Config(model="gpt-4o"),
    )
    assert out == "OK"
    # Second call should include a tool message with the ToolError text
    assert len(calls) == 2
    msgs = calls[1]["messages"]
    assert any(
        m.get("role") == "tool" and m.get("content") == "please validate first" for m in msgs
    )
