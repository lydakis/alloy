from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, AsyncIterable, Awaitable

# This module exists solely for static type checking. The code is wrapped in
# TYPE_CHECKING so it is not executed at runtime (pytest won't run it), but mypy
# will still analyze it. This verifies our .pyi stubs expose the intended types.

if TYPE_CHECKING:
    from alloy import command, ask

    def expects_iter(x: Iterable[str]) -> None: ...
    def expects_aiter(x: AsyncIterable[str]) -> None: ...

    # Sync command: .stream -> Iterable[str], .async_ -> Awaitable[T]
    @command(output=int)
    def Extract() -> str:  # returns a prompt at runtime
        return "extract the number"

    # stream typing
    expects_iter(Extract.stream())

    # async_ typing
    a: Awaitable[int] = Extract.async_()
    _ = a

    # Async command: .stream -> AsyncIterable[str]
    @command(output=str)
    async def Generate() -> str:
        return "write something"

    expects_aiter(Generate.stream())

    # ask.stream_async typing -> AsyncIterable[str]
    expects_aiter(ask.stream_async("hello"))

