from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


def _as_text_from_content(content: Any) -> str:
    try:
        # Claude Messages API returns a list of content blocks
        parts = []
        for block in getattr(content, "content", []) or []:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            else:
                # SDK objects expose .type/.text
                t = getattr(block, "type", None)
                if t == "text":
                    parts.append(getattr(block, "text", ""))
        return "".join(parts) or getattr(content, "text", "") or ""
    except Exception:
        return ""


class AnthropicBackend(ModelBackend):
    """Anthropic Claude backend (minimal implementation).

    This implementation requires the `anthropic` SDK. If it isn't installed,
    calls raise ConfigurationError. Tool-calling support is not implemented in v1.
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
            import anthropic  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install anthropic`."
            ) from e

        client: Any = anthropic.Anthropic()
        # Claude expects system separately; messages are role/content blocks
        system = config.default_system
        messages = [{"role": "user", "content": prompt}]

        # No structured response control for non-object schema in this minimal impl
        if tools:
            # Minimal: expose tool schemas in a hint for future expansion
            pass

        resp = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens or 512,
            temperature=config.temperature,
            messages=messages,
            system=system,
        )
        return _as_text_from_content(resp)

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        # For v1 keep simple and rely on non-streaming for Anthropic
        raise ConfigurationError("Anthropic streaming not implemented in this scaffold")

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        try:
            import anthropic  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install anthropic`."
            ) from e

        client: Any = anthropic.AsyncAnthropic()
        system = config.default_system
        messages = [{"role": "user", "content": prompt}]
        resp = await client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens or 512,
            temperature=config.temperature,
            messages=messages,
            system=system,
        )
        return _as_text_from_content(resp)

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        raise ConfigurationError("Anthropic streaming not implemented in this scaffold")

