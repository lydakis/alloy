from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .config import get_config
from .errors import CommandError
from .models.base import get_backend


class _AskNamespace:
    def __call__(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        context: dict[str, Any] | None = None,
        **overrides,
    ) -> str:
        """Open-ended exploratory interface.

        Example: ask("What is quantum computing?", tools=[search])
        """
        effective = get_config(overrides)
        backend = get_backend(effective.model)
        if context:
            prompt = f"Context: {context}\n\nTask: {prompt}"
        try:
            return backend.complete(
                prompt,
                tools=tools or None,
                output_schema=None,
                config=effective,
            )
        except Exception as e:
            raise CommandError(str(e)) from e

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        context: dict[str, Any] | None = None,
        **overrides,
    ) -> Iterable[str]:
        effective = get_config(overrides)
        backend = get_backend(effective.model)
        if tools:
            raise CommandError("Streaming supports text only; tools are not supported")
        if context:
            prompt = f"Context: {context}\n\nTask: {prompt}"
        try:
            return backend.stream(
                prompt,
                tools=tools or None,
                output_schema=None,
                config=effective,
            )
        except Exception as e:
            raise CommandError(str(e)) from e

    def stream_async(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        context: dict[str, Any] | None = None,
        **overrides,
    ):
        if tools:
            raise CommandError("Streaming supports text only; tools are not supported")

        async def agen():
            effective = get_config(overrides)
            backend = get_backend(effective.model)
            p = f"Context: {context}\n\nTask: {prompt}" if context else prompt
            try:
                aiter = await backend.astream(
                    p,
                    tools=None,
                    output_schema=None,
                    config=effective,
                )
            except Exception as e:
                raise CommandError(str(e)) from e
            async for chunk in aiter:
                yield chunk

        return agen()


ask = _AskNamespace()
