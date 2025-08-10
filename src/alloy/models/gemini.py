from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


class GeminiBackend(ModelBackend):
    """Google Gemini backend (minimal implementation).

    This implementation requires the `google-generativeai` SDK. If it isn't installed,
    calls raise ConfigurationError. Tool-calling and structured outputs are not
    implemented in this scaffold.
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
            import google.generativeai as genai  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "Google Generative AI SDK not installed. Run `pip install google-generativeai`."
            ) from e

        if tools:
            # Not implemented in this scaffold
            raise ConfigurationError("Gemini tool calling not implemented in this scaffold")

        api_key = None  # let the SDK read GOOGLE_API_KEY from env
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(config.model)
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

