from dataclasses import dataclass
import importlib
import typing as t

import pytest
from pytest import MonkeyPatch
from alloy import command, configure
from alloy.config import Config
from alloy.models.base import ModelBackend

pytestmark = pytest.mark.unit


class _SyncBackend(ModelBackend):
    def complete(
        self,
        prompt: str,
        *,
        tools: object | None = None,
        output_schema: dict[str, t.Any] | None = None,
        config: Config,
    ) -> str:
        if (
            output_schema
            and isinstance(output_schema, dict)
            and output_schema.get("type") == "object"
        ):
            return '{"n": 7, "s": "hi"}'
        return "12.5"

    def stream(
        self,
        prompt: str,
        *,
        tools: object | None = None,
        output_schema: dict[str, t.Any] | None = None,
        config: Config,
    ) -> t.Iterator[str]:
        yield "ok"


class _AsyncBackend(ModelBackend):
    async def acomplete(
        self,
        prompt: str,
        *,
        tools: object | None = None,
        output_schema: dict[str, t.Any] | None = None,
        config: Config,
    ) -> str:
        if (
            output_schema
            and isinstance(output_schema, dict)
            and output_schema.get("type") == "object"
        ):
            return '{"n": 7, "s": "hi"}'
        return "3.14"

    async def astream(
        self,
        prompt: str,
        *,
        tools: object | None = None,
        output_schema: dict[str, t.Any] | None = None,
        config: Config,
    ) -> t.AsyncIterator[str]:
        async def agen() -> t.AsyncIterator[str]:
            for part in ("a", "sync"):
                yield part

        return agen()


def _use_sync_backend(monkeypatch: MonkeyPatch) -> None:
    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: _SyncBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: _SyncBackend())


def _use_async_backend(monkeypatch: MonkeyPatch) -> None:
    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: _AsyncBackend())
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: _AsyncBackend())


def test_sync_explicit_output_for_typed_result_primitive(monkeypatch: MonkeyPatch) -> None:
    _use_sync_backend(monkeypatch)
    configure(model="test-model")
    if t.TYPE_CHECKING:

        def price() -> float: ...

    else:

        @command(output=float)
        def price() -> str:
            return "extract price"

    val = price()
    assert isinstance(val, float)
    assert str(val).startswith("12.5")


def test_sync_explicit_output_for_typed_result_dataclass(monkeypatch: MonkeyPatch) -> None:
    _use_sync_backend(monkeypatch)
    configure(model="test-model")

    @dataclass
    class Out:
        n: int
        s: str

    if t.TYPE_CHECKING:

        def build() -> Out: ...

    else:

        @command(output=Out)
        def build() -> str:
            return "build something"

    out = build()
    assert isinstance(out, Out)
    assert out.n == 7 and out.s == "hi"


@pytest.mark.asyncio
async def test_async_explicit_output_for_typed_result_primitive(
    monkeypatch: MonkeyPatch,
) -> None:
    _use_async_backend(monkeypatch)
    configure(model="test-model")
    if t.TYPE_CHECKING:

        async def pi() -> float: ...

    else:

        @command(output=float)
        async def pi() -> str:
            return "pi"

    val = await pi()
    assert isinstance(val, float)
    assert str(val).startswith("3.14")


@pytest.mark.asyncio
async def test_async_explicit_output_for_typed_result_dataclass(
    monkeypatch: MonkeyPatch,
) -> None:
    _use_async_backend(monkeypatch)
    configure(model="test-model")

    @dataclass
    class Out:
        n: int
        s: str

    if t.TYPE_CHECKING:

        async def make() -> Out: ...

    else:

        @command(output=Out)
        async def make() -> str:
            return "make"

    out = await make()
    assert out.n == 7 and out.s == "hi"
