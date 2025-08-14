from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, AsyncIterable, Awaitable, Callable

# Typing-only assertions for the public API surface.

if TYPE_CHECKING:
    from dataclasses import dataclass
    from alloy import command, ask

    def expects_str(x: str) -> None: ...
    def expects_iter(x: Iterable[str]) -> None: ...
    def expects_aiter(x: AsyncIterable[str]) -> None: ...
    def expects_awaitable_int(x: Awaitable[int]) -> None: ...
    def expects_awaitable_str(x: Awaitable[str]) -> None: ...
    def expects_callable_isf_to_float(fn: Callable[[int, str], float]) -> None: ...

    @command(output=int)
    def extract() -> str:
        return "extract the number"

    val_int: int = extract()
    expects_iter(extract.stream())
    expects_awaitable_int(extract.async_())

    @command(output=float)
    def compute(x: int, y: str) -> str:
        return f"compute from {x} and {y}"

    val_float: float = compute(1, "a")
    expects_iter(compute.stream(1, "a"))
    expects_callable_isf_to_float(compute)

    @command(output=float)
    def get_price(text: str) -> str:
        return f"Extract price from: {text}"

    price: float = get_price("the price is 5.99")

    # Default typing when output omitted -> str (sync)
    @command
    def summarize(text: str) -> str:
        return f"Summarize: {text}"

    summary: str = summarize("hello")
    expects_iter(summarize.stream("hello"))

    @command(output=str)
    async def generate() -> str:
        return "write something"

    expects_awaitable_str(generate())
    expects_aiter(generate.stream())
    expects_awaitable_str(generate.async_())

    # Default typing when output omitted -> str (async)
    @command
    async def a_summarize() -> str:
        return "hi"

    expects_awaitable_str(a_summarize())
    expects_aiter(a_summarize.stream())
    expects_awaitable_str(a_summarize.async_())

    @dataclass
    class Out:
        value: int
        label: str

    @command(output=Out)
    def make() -> str:
        return "make output"

    out_val: Out = make()
    from typing import Awaitable as _Awaitable

    out_await: _Awaitable[Out] = make.async_()

    expects_str(ask("hello"))
    expects_iter(ask.stream("hello"))
    expects_aiter(ask.stream_async("hello"))
