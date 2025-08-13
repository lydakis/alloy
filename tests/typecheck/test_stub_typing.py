from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, AsyncIterable, Awaitable

# This module exists solely for static type checking. The code is wrapped in
# TYPE_CHECKING so it is not executed at runtime (pytest won't run it), but mypy
# will still analyze it. This verifies our .pyi stubs expose the intended types.

if TYPE_CHECKING:
    from alloy import command, ask

    def expects_iter(x: Iterable[str]) -> None: ...
    def expects_aiter(x: AsyncIterable[str]) -> None: ...

    # Sync command via eager form: .stream -> Iterable[str], .async_ -> Awaitable[T]
    def _extract_impl() -> str:
        return "extract the number"

    Extract = command(_extract_impl, output=int)
    expects_iter(Extract.stream())
    a: Awaitable[int] = Extract.async_()
    _ = a

    # Async command via eager form: .stream -> AsyncIterable[str]
    async def _generate_impl() -> str:
        return "write something"

    Generate = command(_generate_impl, output=str)
    expects_aiter(Generate.stream())

    # ask.stream_async typing -> Awaitable[AsyncIterable[str]] (must be awaited)
    def expects_awaitable(x: Awaitable[AsyncIterable[str]]) -> None: ...

    expects_awaitable(ask.stream_async("hello"))
