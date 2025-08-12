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
        model_name = config.model or "gemini-2.5-pro"
        # Prefer structured output when schema is provided; Gemini supports
        # response_mime_type + response_schema for JSON. If primitive, wrap.
        generation_config = {}
        wrapped_primitive = False
        schema = None
        if output_schema and isinstance(output_schema, dict):
            schema = output_schema
            if schema.get("type") != "object":
                schema = {
                    "type": "object",
                    "properties": {"value": output_schema},
                    "required": ["value"],
                }
                wrapped_primitive = True
            generation_config = {
                "response_mime_type": "application/json",
                "response_schema": schema,
            }

        try:
            if generation_config:
                res_new = client.models.generate_content(
                    model=model_name, contents=prompt, generation_config=generation_config
                )
                text = getattr(res_new, "text", "") or ""
                if wrapped_primitive and text:
                    import json as _json

                    try:
                        data = _json.loads(text)
                        if isinstance(data, dict) and "value" in data:
                            return str(data["value"])
                    except Exception:
                        pass
                return text
        except Exception:
            # Fallback to non-structured call below
            pass

        # Non-structured fallback
        res_new = client.models.generate_content(model=model_name, contents=prompt)
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
