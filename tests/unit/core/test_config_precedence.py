import importlib
import pytest

from alloy.config import get_config, configure, _reset_config_for_tests
from alloy import ask, command

pytestmark = pytest.mark.unit


def test_get_config_precedence_env_global_overrides(monkeypatch):
    _reset_config_for_tests()
    monkeypatch.setenv("ALLOY_MODEL", "env-model")
    cfg = get_config()
    assert cfg.model == "env-model"

    configure(model="global-model", temperature=0.1)
    cfg2 = get_config()
    assert cfg2.model == "global-model"
    assert cfg2.temperature == 0.1

    cfg3 = get_config({"model": "call-model", "temperature": 0.0})
    assert cfg3.model == "call-model"
    assert cfg3.temperature == 0.0


def test_command_decorator_overrides_env_and_global(monkeypatch):
    _reset_config_for_tests()
    monkeypatch.setenv("ALLOY_MODEL", "env-model")
    configure(model="global-model")

    captured = {}

    class _CapBackend:
        def complete(self, prompt: str, *, tools=None, output_schema=None, config=None) -> str:
            captured["model"] = config.model
            captured["temperature"] = config.temperature
            return "ok"

    _cmd_mod = importlib.import_module("alloy.command")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: _CapBackend())

    @command(output=str, model="decor-model", temperature=0.2)
    def run() -> str:
        return "hi"

    out = run()
    assert out == "ok"
    assert captured["model"] == "decor-model"
    assert captured["temperature"] == 0.2


def test_ask_callsite_overrides(monkeypatch):
    _reset_config_for_tests()
    configure(model="global", temperature=0.3)

    class _CapBackend:
        def complete(self, prompt: str, *, tools=None, output_schema=None, config=None) -> str:
            assert config.default_system == "You are helpful"
            return "ok"

        def stream(self, *a, **k):
            return iter(["x"])

    ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(ask_mod, "get_backend", lambda model: _CapBackend())

    out = ask("hello", system="You are helpful")
    assert out == "ok"
