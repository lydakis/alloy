from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError


class ModelBackend:
    """Abstract provider interface.

    Concrete backends implement completion and tool-calling behavior.
    """

    def complete(
        self,
        prompt: str,
        *,
        tools: Optional[list] = None,
        output_schema: Optional[dict] = None,
        config: Config,
    ) -> str:
        raise NotImplementedError

    def stream(
        self,
        prompt: str,
        *,
        tools: Optional[list] = None,
        output_schema: Optional[dict] = None,
        config: Config,
    ) -> Iterable[str]:
        raise NotImplementedError

    # Async variants
    async def acomplete(
        self,
        prompt: str,
        *,
        tools: Optional[list] = None,
        output_schema: Optional[dict] = None,
        config: Config,
    ) -> str:
        raise NotImplementedError

    async def astream(
        self,
        prompt: str,
        *,
        tools: Optional[list] = None,
        output_schema: Optional[dict] = None,
        config: Config,
    ) -> AsyncIterable[str]:
        raise NotImplementedError


def get_backend(model: str | None) -> ModelBackend:
    if not model:
        raise ConfigurationError(
            "No model configured. Call alloy.configure(model=...) first."
        )
    name = model.lower()
    if name.startswith("gpt") or name.startswith("openai") or "gpt-" in name:
        from .openai import OpenAIBackend

        return OpenAIBackend()

    # Future: route to Anthropic/Gemini/Local or ReAct fallback
    raise ConfigurationError(
        f"No backend available for model '{model}'."
    )
