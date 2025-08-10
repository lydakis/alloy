from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


def _extract_model_name(model: str | None) -> str:
    if not model:
        return ""
    # Accept prefixes like "ollama:phi3"
    if model.startswith("ollama:"):
        return model.split(":", 1)[1]
    if model.startswith("local:"):
        return model.split(":", 1)[1]
    return model


class OllamaBackend(ModelBackend):
    """Ollama backend using the `ollama` Python SDK.

    Tool-calling and streaming are not implemented in this scaffold.
    """

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        try:
            import ollama
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "Ollama SDK not installed. Run `pip install alloy[ollama]`."
            ) from e

        if tools:
            raise ConfigurationError("Ollama tool calling not implemented in this scaffold")

        model_name = _extract_model_name(config.model)
        if not model_name:
            raise ConfigurationError("Ollama model not specified (use model='ollama:<name>')")

        # Use chat API for consistency with role/content messaging
        messages = [{"role": "user", "content": prompt}]
        try:
            res = ollama.chat(model=model_name, messages=messages)
            msg = res.get("message", {}) if isinstance(res, dict) else getattr(res, "message", {})
            return msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        except Exception as e:
            raise ConfigurationError(str(e)) from e

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        raise ConfigurationError("Ollama streaming not implemented in this scaffold")

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        # The SDK is synchronous; bridge via thread if needed in future
        return self.complete(prompt, tools=tools, output_schema=output_schema, config=config)

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        raise ConfigurationError("Ollama streaming not implemented in this scaffold")
