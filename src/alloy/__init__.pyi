from typing import Any, Callable, ParamSpec, TypeVar, overload, Coroutine, Iterable

P = ParamSpec("P")
T = TypeVar("T")

# Public API re-exports (for type checkers)
from .errors import CommandError, ToolError, ConfigurationError


# Decorator overloads for sync/async
@overload
def command(__func: Callable[P, str], /, *, output: type[T] | None = ..., tools: list[Callable[..., Any]] | None = ..., model: str | None = ..., temperature: float | None = ..., max_tokens: int | None = ..., system: str | None = ..., retry: int | None = ..., retry_on: type[BaseException] | None = ...) -> Callable[P, T]: ...

@overload
def command(__func: Callable[P, Coroutine[Any, Any, str]], /, *, output: type[T] | None = ..., tools: list[Callable[..., Any]] | None = ..., model: str | None = ..., temperature: float | None = ..., max_tokens: int | None = ..., system: str | None = ..., retry: int | None = ..., retry_on: type[BaseException] | None = ...) -> Callable[P, Coroutine[Any, Any, T]]: ...

@overload
def command(*, output: type[T] | None = ..., tools: list[Callable[..., Any]] | None = ..., model: str | None = ..., temperature: float | None = ..., max_tokens: int | None = ..., system: str | None = ..., retry: int | None = ..., retry_on: type[BaseException] | None = ...) -> Callable[[Callable[P, str]], Callable[P, T]]: ...


class _AskNamespace:
    def __call__(self, prompt: str, *, tools: list[Callable[..., Any]] | None = ..., context: dict[str, Any] | None = ..., **overrides: Any) -> str: ...
    def stream(self, prompt: str, *, tools: list[Callable[..., Any]] | None = ..., context: dict[str, Any] | None = ..., **overrides: Any) -> Iterable[str]: ...
    async def stream_async(self, prompt: str, *, tools: list[Callable[..., Any]] | None = ..., context: dict[str, Any] | None = ..., **overrides: Any) -> Any: ...


# Runtime values provided by the package
def tool(__func: Callable[..., Any] | None = ..., /, **kwargs: Any) -> Any: ...
def require(predicate: Callable[[Any], bool], message: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
def ensure(predicate: Callable[[Any], bool], message: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
def configure(**kwargs: Any) -> None: ...
# Implementation provided at runtime
ask: _AskNamespace

__all__ = [
    "command",
    "tool",
    "require",
    "ensure",
    "ask",
    "configure",
    "CommandError",
    "ToolError",
    "ConfigurationError",
]
