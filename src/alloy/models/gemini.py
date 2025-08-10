from __future__ import annotations

from collections.abc import Iterable, AsyncIterable

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


class GeminiBackend(ModelBackend):
    """Google Gemini backend (minimal implementation).

    Supports the `google-genai` SDK. If it isn't installed, calls raise
    ConfigurationError. Tool-calling and structured outputs are not implemented
    in this scaffold.
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
            from google import genai as genai_new
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "Google GenAI SDK not installed. Install `alloy[gemini]`."
            ) from e

        if tools:
            raise ConfigurationError("Gemini tool calling not implemented in this scaffold")

        client = genai_new.Client()  # reads GOOGLE_API_KEY from env
        # Minimal call; omit advanced config for now
        res_new = client.models.generate_content(
            model=(config.model or "gemini-1.5-pro"), contents=prompt
        )
        try:
            return getattr(res_new, "text", "") or ""
        except Exception:
            return ""

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        raise ConfigurationError("Gemini streaming not implemented in this scaffold")

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        # google-generativeai does not expose an async client in the basic SDK
        # Provide a simple synchronous bridge (users should call sync APIs for now)
        return self.complete(prompt, tools=tools, output_schema=output_schema, config=config)

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        raise ConfigurationError("Gemini streaming not implemented in this scaffold")
