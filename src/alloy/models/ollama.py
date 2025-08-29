from __future__ import annotations

from collections.abc import Iterable, AsyncIterable

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


def _extract_model_name(model: str | None) -> str:
    if not model:
        return ""
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
        except Exception as e:
            raise ConfigurationError(
                "Ollama SDK not installed. Run `pip install alloy[ollama]`."
            ) from e

        if tools:
            raise ConfigurationError("Ollama tool calling not implemented in this scaffold")

        model_name = _extract_model_name(config.model)
        if not model_name:
            raise ConfigurationError("Ollama model not specified (use model='ollama:<name>')")

        if isinstance(output_schema, dict):
            t = output_schema.get("type")
            if t in ("number", "integer", "boolean", "string"):
                example = {
                    "number": '{"value": 3.14}',
                    "integer": '{"value": 7}',
                    "boolean": '{"value": true}',
                    "string": '{"value": "text"}',
                }[t]
                prompt = (
                    f"{prompt}\n\nInstructions: Return only a JSON object with a single key 'value' "
                    f"matching the required type. No code fences or extra text.\nExample: {example}"
                )

        messages = [{"role": "user", "content": prompt}]
        try:
            res = ollama.chat(model=model_name, messages=messages)
            msg = res.get("message", {}) if isinstance(res, dict) else getattr(res, "message", {})
            content = (
                msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
            )
            if isinstance(output_schema, dict):
                t = output_schema.get("type")
                if t in ("number", "integer", "boolean", "string"):
                    import json as _json

                    try:
                        data = _json.loads(content)
                        if isinstance(data, dict) and "value" in data:
                            return str(data["value"])
                    except Exception:
                        pass
                    messages.append({"role": "assistant", "content": content or ""})
                    strict = (
                        "Return only a JSON object with a single key 'value' matching the required type. "
                        "No code fences or extra text."
                    )
                    messages.append({"role": "user", "content": strict})
                    res2 = ollama.chat(model=model_name, messages=messages)
                    msg2 = (
                        res2.get("message", {})
                        if isinstance(res2, dict)
                        else getattr(res2, "message", {})
                    )
                    content2 = (
                        msg2.get("content", "")
                        if isinstance(msg2, dict)
                        else getattr(msg2, "content", "")
                    )
                    try:
                        data2 = _json.loads(content2)
                        if isinstance(data2, dict) and "value" in data2:
                            return str(data2["value"])
                    except Exception:
                        pass
            return content
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
