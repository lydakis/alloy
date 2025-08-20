from __future__ import annotations

import importlib
import pytest

from alloy import command, ConfigurationError


def use_fake_backend(monkeypatch):
    from alloy.models.base import ModelBackend
    from alloy.config import Config

    class FakeBackend(ModelBackend):
        def __init__(self):
            self.calls = 0

        def complete(self, prompt: str, *, tools=None, output_schema=None, config: Config) -> str:
            self.calls += 1
            if (
                output_schema
                and isinstance(output_schema, dict)
                and output_schema.get("type") == "object"
            ):
                return '{"value": 42, "label": "ok"}'
            return "12.5"

        def stream(self, prompt: str, *, tools=None, output_schema=None, config: Config):
            yield "hel"
            yield "lo"

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: FakeBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: FakeBackend())


def test_open_ended_dict_output_raises(monkeypatch):
    use_fake_backend(monkeypatch)

    @command(output=dict)
    def make() -> str:
        return "make object"

    with pytest.raises(ConfigurationError) as ei:
        _ = make()
    assert "Strict Structured Outputs do not support open-ended dict" in str(ei.value)


def test_list_of_dict_output_raises(monkeypatch):
    use_fake_backend(monkeypatch)

    @command(output=list[dict])
    def make_list() -> str:
        return "make objects"

    with pytest.raises(ConfigurationError) as ei:
        _ = make_list()
    assert "Strict Structured Outputs do not support open-ended dict" in str(ei.value)
