from __future__ import annotations

import importlib
import pytest

from alloy import command, ConfigurationError, CommandError
from alloy.config import Config
from alloy.models.base import ModelBackend


def test_rejects_non_str_function_return_annotation():
    # Intentionally wrong authoring: command functions must be annotated -> str.
    def bad() -> int:
        return 1

    with pytest.raises(ConfigurationError):
        _ = command(output=int)(bad)


def test_type_mismatch_after_parse_raises(monkeypatch):
    class FakeBackend(ModelBackend):
        def complete(self, prompt: str, *, tools=None, output_schema=None, config: Config) -> str:
            return "[]"

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: FakeBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: FakeBackend())

    from dataclasses import dataclass

    @dataclass
    class Out:
        n: int
        s: str

    @command(output=Out)
    def build() -> str:
        return "make"

    with pytest.raises(CommandError):
        _ = build()
