import importlib
import pytest
from alloy import ask, configure
from alloy.config import Config
from alloy.models.base import ModelBackend

pytestmark = pytest.mark.unit


class FakeBackend(ModelBackend):
    def __init__(self):
        self.last_config: Config | None = None

    def complete(self, prompt: str, *, tools=None, output_schema=None, config: Config) -> str:
        self.last_config = config
        return "ok"


def test_ask_per_call_system_alias(monkeypatch):
    fb = FakeBackend()
    ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(ask_mod, "get_backend", lambda model: fb)

    configure(model="test-model")

    out = ask("hi", system="You are helpful")
    assert out == "ok"
    assert fb.last_config is not None
    assert fb.last_config.default_system == "You are helpful"
