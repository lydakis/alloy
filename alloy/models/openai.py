from __future__ import annotations

from collections.abc import Iterable, AsyncIterable

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


class OpenAIBackend(ModelBackend):
    """Placeholder OpenAI backend.

    This scaffold does not include network calls. The methods
    raise ConfigurationError to indicate missing runtime integration.
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
            from openai import OpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        client = OpenAI()
        messages = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        tool_schemas = None
        tool_map: dict[str, any] = {}
        if tools:
            tool_schemas = [
                {"type": "function", "function": t.spec.as_schema()} for t in tools
            ]
            tool_map = {t.spec.name: t for t in tools}

        # Attempt structured output via JSON schema if provided
        response_format = None
        if output_schema and isinstance(output_schema, dict):
            if output_schema.get("type") == "object":
                response_format = {
                    "type": "json_schema",
                    "json_schema": {"name": "alloy_output", "schema": output_schema},
                }
            else:
                # Encourage JSON even for non-object schemas
                response_format = {"type": "json_object"}

        while True:
            is_gpt5 = bool(config.model and "gpt-5" in config.model)
            kwargs = {
                "model": config.model,
                "messages": messages,
            }
            if tool_schemas is not None:
                kwargs["tools"] = tool_schemas
                kwargs["tool_choice"] = "auto"
            if (config.temperature is not None) and not is_gpt5:
                kwargs["temperature"] = config.temperature
            if config.max_tokens is not None:
                kwargs["max_tokens"] = config.max_tokens
            if response_format is not None:
                kwargs["response_format"] = response_format
            resp = client.chat.completions.create(**kwargs)

            choice = resp.choices[0]
            msg = choice.message
            tool_calls = getattr(msg, "tool_calls", None)

            if tool_calls:
                # Execute tools and append tool results, then continue the loop
                for tc in tool_calls:
                    name = tc.function.name
                    args = tc.function.arguments or "{}"
                    tool = tool_map.get(name)
                    if not tool:
                        content = f"Tool '{name}' not available."
                    else:
                        import json

                        try:
                            parsed = json.loads(args)
                        except Exception:
                            parsed = {}
                        # Call tool with kwargs
                        result = tool(**parsed) if isinstance(parsed, dict) else tool(parsed)
                        try:
                            content = json.dumps(result)
                        except Exception:
                            content = str(result)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": name,
                            "content": content,
                        }
                    )
                # Also append the assistant message that requested tool calls
                messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [tc for tc in tool_calls]})
                continue

            # Return final content
            return msg.content or ""

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        if tools:
            # Streaming with tool calling adds complexity; keep simple for v1
            raise ConfigurationError("Streaming with tools is not supported yet")

        client = OpenAI()
        messages = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        is_gpt5 = bool(config.model and "gpt-5" in config.model)
        kwargs = {
            "model": config.model,
            "messages": messages,
            "stream": True,
        }
        if (config.temperature is not None) and not is_gpt5:
            kwargs["temperature"] = config.temperature
        if config.max_tokens is not None:
            kwargs["max_tokens"] = config.max_tokens
        stream = client.chat.completions.create(**kwargs)
        def gen():
            for event in stream:
                try:
                    delta = event.choices[0].delta.content or ""
                except Exception:
                    delta = ""
                if delta:
                    yield delta
        return gen()

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        client = AsyncOpenAI()
        messages = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        tool_schemas = None
        tool_map: dict[str, any] = {}
        if tools:
            tool_schemas = [
                {"type": "function", "function": t.spec.as_schema()} for t in tools
            ]
            tool_map = {t.spec.name: t for t in tools}

        response_format = None
        if output_schema and isinstance(output_schema, dict):
            if output_schema.get("type") == "object":
                response_format = {
                    "type": "json_schema",
                    "json_schema": {"name": "alloy_output", "schema": output_schema},
                }
            else:
                response_format = {"type": "json_object"}

        while True:
            is_gpt5 = bool(config.model and "gpt-5" in config.model)
            kwargs = {
                "model": config.model,
                "messages": messages,
            }
            if tool_schemas is not None:
                kwargs["tools"] = tool_schemas
                kwargs["tool_choice"] = "auto"
            if (config.temperature is not None) and not is_gpt5:
                kwargs["temperature"] = config.temperature
            if config.max_tokens is not None:
                kwargs["max_tokens"] = config.max_tokens
            if response_format is not None:
                kwargs["response_format"] = response_format
            resp = await client.chat.completions.create(**kwargs)
            choice = resp.choices[0]
            msg = choice.message
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    name = tc.function.name
                    args = tc.function.arguments or "{}"
                    tool = tool_map.get(name)
                    if not tool:
                        content = f"Tool '{name}' not available."
                    else:
                        import json

                        try:
                            parsed = json.loads(args)
                        except Exception:
                            parsed = {}
                        result = tool(**parsed) if isinstance(parsed, dict) else tool(parsed)
                        try:
                            content = json.dumps(result)
                        except Exception:
                            content = str(result)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": name,
                            "content": content,
                        }
                    )
                messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [tc for tc in tool_calls]})
                continue
            return msg.content or ""

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        if tools:
            raise ConfigurationError("Streaming with tools is not supported yet")

        client = AsyncOpenAI()
        messages = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": config.model,
            "messages": messages,
            "stream": True,
        }
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if config.max_tokens is not None:
            kwargs["max_tokens"] = config.max_tokens
        stream = await client.chat.completions.create(**kwargs)

        async def agen():
            async for event in stream:
                try:
                    delta = event.choices[0].delta.content or ""
                except Exception:
                    delta = ""
                if delta:
                    yield delta

        return agen()
