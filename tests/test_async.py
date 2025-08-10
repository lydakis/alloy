from dataclasses import dataclass

import importlib

import pytest

from alloy import command, configure
from alloy.models.base import ModelBackend
from alloy.config import Config


class AsyncFakeBackend(ModelBackend):
    def __init__(self):
        self.calls = 0

    async def acomplete(
        self, prompt: str, *, tools=None, output_schema=None, config: Config
    ) -> str:
        self.calls += 1
        if (
            output_schema
            and isinstance(output_schema, dict)
            and output_schema.get("type") == "object"
        ):
            return '{"n": 7, "s": "hi"}'
        return "3.14"

    async def astream(self, prompt: str, *, tools=None, output_schema=None, config: Config):
        async def agen():
            for part in ("a", "sync"):
                yield part

        return agen()


def use_async_backend(monkeypatch):
    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: AsyncFakeBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: AsyncFakeBackend())


@pytest.mark.asyncio
async def test_async_command_returns_value(monkeypatch):
    use_async_backend(monkeypatch)
    configure(model="test-model")

    @dataclass
    class Out:
        n: int
        s: str

    @command(output=Out)
    async def Build() -> str:
        return "make"

    result = await Build()
    assert result.n == 7 and result.s == "hi"


@pytest.mark.asyncio
async def test_async_command_stream(monkeypatch):
    use_async_backend(monkeypatch)
    configure(model="test-model")

    @command(output=str)
    async def Generate() -> str:
        return "stream it"

    got = []
    async for chunk in Generate.stream():
        got.append(chunk)
    assert "".join(got) == "async"


@pytest.mark.asyncio
async def test_sync_command_async_convenience(monkeypatch):
    use_async_backend(monkeypatch)
    configure(model="test-model")

    @command(output=float)
    def Pi() -> str:
        return "pi"

    val = await Pi.async_()
    assert isinstance(val, float)
    assert str(val).startswith("3.14")
