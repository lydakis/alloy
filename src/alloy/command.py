from __future__ import annotations

import inspect
from collections.abc import Iterable
from typing import Any, Callable, NoReturn
from .config import get_config
from .errors import CommandError, ConfigurationError
from .models.base import get_backend
from .tool import ToolCallable, ToolSpec
from .types import to_json_schema, parse_output


_MISSING: Any = object()


def command(
    fn: Callable[..., Any] | None = None,
    *,
    output: Any = _MISSING,
    tools: list[Callable[..., Any]] | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    system: str | None = None,
    retry: int | None = None,
    retry_on: type[BaseException] | None = None,
):
    """Decorator to declare an AI-powered command.

    The wrapped function returns an English prompt specification. This executes
    the model with optional tools and parses the result into the annotated
    return type. The `retry` parameter represents total attempts (minimum 1).
    """

    def wrap(func: Callable[..., Any]):
        try:
            from typing import get_type_hints as _get_hints

            ra = _get_hints(func).get("return", None)
        except Exception:
            ra = None
        if ra is not None and ra is not str:
            raise ConfigurationError(
                "@command functions must be annotated as -> str; the function returns the prompt, and the decorator controls the output type."
            )
        if output is _MISSING:
            out_type = None
        elif output is None:
            out_type = type(None)
        else:
            out_type = output
        return Command(
            func,
            output_type=out_type,
            tools=tools or [],
            per_command_cfg={
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "default_system": system,
                "retry": retry,
                "retry_on": retry_on,
            },
        )

    if fn is not None:
        return wrap(fn)
    return wrap


class _CommandHelpers:
    _output_type: type | None

    def _parse_or_return(self, text: Any):
        if self._output_type is type(None):
            return None
        if self._output_type is None:
            if isinstance(text, str) and not text.strip():
                raise CommandError(
                    "Model produced no output. Specify output=... in @command or use alloy.ask for open-ended queries."
                )
            return text
        if isinstance(text, str) and not text.strip():
            expected = getattr(self._output_type, "__name__", str(self._output_type))
            raise CommandError(
                f"Model produced no output; expected {expected}. Increase max_tool_turns or ensure the model returns a final answer."
            )
        try:
            value = parse_output(self._output_type, text)
        except Exception as parse_exc:
            expected = getattr(self._output_type, "__name__", str(self._output_type))
            snippet = (text[:120] + "…") if isinstance(text, str) and len(text) > 120 else text
            raise CommandError(
                f"Failed to parse model output as {expected}: {snippet!r}"
            ) from parse_exc
        if not _is_instance_of(value, self._output_type):
            expected = getattr(self._output_type, "__name__", str(self._output_type))
            raise CommandError(f"Model output type mismatch; expected {expected}.")
        return value

    def _should_break_retry(self, retry_on: type[BaseException] | None, exc: Exception) -> bool:
        return bool(retry_on and not isinstance(exc, retry_on))

    def _raise_after_retries(self, last_err: Exception | None, attempts: int) -> NoReturn:
        if isinstance(last_err, CommandError):
            raise last_err
        if last_err is not None:
            raise CommandError(f"Command failed after {attempts} attempts") from last_err
        raise CommandError("Unknown command error after exhausting retries")


class Command(_CommandHelpers):
    def __init__(
        self,
        func: Callable[..., Any],
        *,
        output_type: type | None,
        tools: list[Callable[..., Any]],
        per_command_cfg: dict[str, Any],
    ):
        self._func = func
        self._output_type = output_type
        self._tools = [
            t if isinstance(t, ToolCallable) else ToolCallable(_to_spec(t)) for t in tools
        ]
        self._cfg = {k: v for k, v in per_command_cfg.items() if v is not None}
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self._is_async = inspect.iscoroutinefunction(func)

    def __call__(self, *args, **kwargs):
        if self._is_async:
            return self.async_(*args, **kwargs)
        prompt = self._func(*args, **kwargs)
        if not isinstance(prompt, str):
            prompt = str(prompt)
        effective = get_config(self._cfg)
        backend = get_backend(effective.model)

        try:
            output_schema = to_json_schema(self._output_type) if self._output_type else None
        except ValueError as e:
            raise ConfigurationError(str(e)) from e

        attempts = max(int(effective.retry or 1), 1)
        last_err: Exception | None = None
        for _ in range(attempts):
            try:
                text = backend.complete(
                    prompt,
                    tools=self._tools or None,
                    output_schema=output_schema,
                    config=effective,
                )
                return self._parse_or_return(text)
            except Exception as e:
                last_err = e
                if self._should_break_retry(effective.retry_on, e):
                    break
        self._raise_after_retries(last_err, attempts)

    def stream(self, *args, **kwargs) -> Iterable[str] | Any:
        if self._tools or (self._output_type is not None and self._output_type is not str):
            raise ConfigurationError(
                "Streaming supports text-only commands; tools and non-string typed outputs are not supported"
            )

        effective = get_config(self._cfg)
        backend = get_backend(effective.model)
        output_schema = None

        if not self._is_async:
            prompt = self._func(*args, **kwargs)
            if not isinstance(prompt, str):
                prompt = str(prompt)
            try:
                return backend.stream(
                    prompt,
                    tools=None,
                    output_schema=output_schema,
                    config=effective,
                )
            except Exception as e:
                raise CommandError(str(e)) from e

        async def agen():
            prompt_val = await self._func(*args, **kwargs)
            if not isinstance(prompt_val, str):
                prompt_str = str(prompt_val)
            else:
                prompt_str = prompt_val
            try:
                aiter = await backend.astream(
                    prompt_str,
                    tools=None,
                    output_schema=None,
                    config=effective,
                )
            except Exception as e:
                raise CommandError(str(e)) from e
            async for chunk in aiter:
                yield chunk

        return agen()

    async def async_(self, *args, **kwargs):
        if self._is_async:
            prompt_val = await self._func(*args, **kwargs)
        else:
            prompt_val = self._func(*args, **kwargs)
        if not isinstance(prompt_val, str):
            prompt = str(prompt_val)
        else:
            prompt = prompt_val
        effective = get_config(self._cfg)
        backend = get_backend(effective.model)
        output_schema = to_json_schema(self._output_type) if self._output_type else None

        attempts = max(int(effective.retry or 1), 1)
        last_err: Exception | None = None
        for _ in range(attempts):
            try:
                text = await backend.acomplete(
                    prompt,
                    tools=self._tools or None,
                    output_schema=output_schema,
                    config=effective,
                )
                return self._parse_or_return(text)
            except Exception as e:
                last_err = e
                if self._should_break_retry(effective.retry_on, e):
                    break
        self._raise_after_retries(last_err, attempts)


def _to_spec(func: Callable[..., Any]) -> ToolSpec:
    spec = getattr(func, "_alloy_tool_spec", None)
    if spec is not None:
        return spec
    from .tool import ToolSpec as TS
    import inspect as _inspect

    return TS(
        func=func,
        name=func.__name__,
        description=(_inspect.getdoc(func) or "").strip(),
        signature=str(_inspect.signature(func)),
    )


def _is_instance_of(value: Any, tp: Any) -> bool:
    try:
        from .types import is_dataclass_type, is_typeddict_type
        from typing import get_origin
    except Exception:
        return isinstance(value, tp)
    if tp is Any:
        return True
    if tp in (str, int, float, bool):
        return isinstance(value, tp)
    if is_dataclass_type(tp):
        return isinstance(value, tp)
    if is_typeddict_type(tp):
        return isinstance(value, dict)
    origin = get_origin(tp)
    if origin is list:
        return isinstance(value, list)
    if origin is dict:
        return isinstance(value, dict)
    if tp is type(None):
        return value is None
    return isinstance(value, tp)
