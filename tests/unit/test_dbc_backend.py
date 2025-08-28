from __future__ import annotations

import importlib
import pytest

from alloy import tool, ensure, command, configure
from alloy.config import Config
from alloy import ToolError
from alloy.models.base import ModelBackend

pytestmark = [pytest.mark.unit, pytest.mark.contracts]


class DbcFakeBackend(ModelBackend):
    def complete(self, prompt: str, *, tools=None, output_schema=None, config: Config) -> str:
        if tools:
            t = tools[0]
            try:
                return str(t(n=3))
            except ToolError as e:
                return str(e)
            except Exception as e:
                return f"tool_error:{e}"
        return ""


def test_backend_surfaces_contract_message_via_fake(monkeypatch):
    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: DbcFakeBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: DbcFakeBackend())
    configure(model="test-model")

    @tool
    @ensure(lambda r: isinstance(r, int) and r % 2 == 0, "must be even")
    def square(n: int) -> int:
        return n * n

    @command(output=str, tools=[square])
    def check() -> str:
        return (
            "Use the tool square(n=3) now. If the tool returns a plain message, output that "
            "message exactly with no extra text."
        )

    out = check()
    assert isinstance(out, str)
    assert "must be even" in out.lower()
