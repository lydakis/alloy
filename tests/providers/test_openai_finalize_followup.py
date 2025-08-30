from __future__ import annotations

import importlib
import pytest

from alloy import command, configure

pytestmark = pytest.mark.providers


class _FakeResponses:
    def __init__(self) -> None:
        self.calls = 0
        self.history: list[dict] = []

    def create(self, **kwargs):
        self.calls += 1
        self.history.append(kwargs)
        if self.calls == 1:
            return {"id": "r1", "output": []}
        return {"id": "r2", "output_text": "ok"}


class _FakeOpenAI:
    last: "_FakeOpenAI | None" = None

    def __init__(self) -> None:
        self.responses = _FakeResponses()
        _FakeOpenAI.last = self


def test_openai_finalize_one_shot(monkeypatch):
    from alloy.models.openai import OpenAIBackend

    be = OpenAIBackend()
    be._OpenAI = _FakeOpenAI

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: be)
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: be)

    configure(model="gpt-5-mini", auto_finalize_missing_output=True)

    @command(output=str)
    def hello() -> str:
        return "Say OK"

    out = hello()
    assert out.strip().lower() == "ok"

    fc = _FakeOpenAI.last
    assert fc is not None
    hist = fc.responses.history
    assert len(hist) == 2
    assert "previous_response_id" not in hist[0]
    assert hist[1].get("previous_response_id") == "r1"
