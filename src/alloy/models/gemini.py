from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


class GeminiBackend(ModelBackend):
    """Google Gemini backend (minimal implementation).

    Supports either the new `google-genai` SDK (preferred) or the legacy
    `google-generativeai` SDK. If neither is installed, calls raise
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
        # Prefer the new GA SDK if available
        try:
            from google import genai as genai_new  # type: ignore

            if tools:
                raise ConfigurationError("Gemini tool calling not implemented in this scaffold")

            client = genai_new.Client()  # reads GOOGLE_API_KEY from env
            # Minimal call; omit advanced config for now
            res = client.models.generate_content(
                model=config.model or "gemini-1.5-pro", contents=prompt
            )
            try:
                return getattr(res, "text", "") or ""
            except Exception:
                return ""
        except Exception:
            # Fallback to legacy SDK
            try:
                import google.generativeai as genai_legacy  # type: ignore
            except Exception as e:  # pragma: no cover
                raise ConfigurationError(
                    "Google GenAI SDK not installed. Install `alloy[gemini]` (new) or `alloy[gemini-legacy]`."
                ) from e

            if tools:
                raise ConfigurationError("Gemini tool calling not implemented in this scaffold")

            api_key = None  # let the SDK read GOOGLE_API_KEY from env
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel(config.model)
            kwargs: dict[str, Any] = {}
            if config.temperature is not None:
                kwargs.setdefault("generation_config", {})["temperature"] = config.temperature
            res = model.generate_content(prompt, **kwargs)
            try:
                return res.text or ""
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
