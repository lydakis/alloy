from __future__ import annotations

import importlib
from dataclasses import dataclass

import pytest

from alloy import command, CommandError

pytestmark = [pytest.mark.unit, pytest.mark.errors]


class BlankBackend:
    def complete(self, prompt: str, *, tools=None, output_schema=None, config=None) -> str:
        return ""


def use_blank_backend(monkeypatch):
    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: BlankBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: BlankBackend())


def test_typed_command_raises_on_missing_output(monkeypatch):
    use_blank_backend(monkeypatch)

    @command(output=float)
    def calc() -> str:
        return "do calc"

    with pytest.raises(CommandError) as ei:
        _ = calc()
    assert "produced no output" in str(ei.value)


def test_dataclass_command_raises_on_missing_output(monkeypatch):
    use_blank_backend(monkeypatch)

    @dataclass
    class Out:
        a: int
        b: str

    @command(output=Out)
    def build() -> str:
        return "make it"

    with pytest.raises(CommandError) as ei:
        _ = build()
    assert "produced no output" in str(ei.value)


def test_output_none_returns_none(monkeypatch):
    use_blank_backend(monkeypatch)

    @command(output=None)
    def side_effect() -> str:
        return "do something"

    result = side_effect()
    assert result is None


def test_untyped_command_raises_on_missing_output(monkeypatch):
    use_blank_backend(monkeypatch)


@command
def gen() -> str:
    return "generate"

    with pytest.raises(CommandError) as ei:
        _ = gen()
    assert "produced no output" in str(ei.value)
