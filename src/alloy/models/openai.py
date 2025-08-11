from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


class OpenAIBackend(ModelBackend):
    """OpenAI backend using Chat Completions.

    Requires the `openai` SDK. If it is not installed, a ConfigurationError is raised
    at call time so importing the module does not crash users without the SDK.
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
            from openai import OpenAI
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        client: Any = OpenAI()
        messages: list[dict[str, Any]] = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        tool_schemas = None
        tool_map: dict[str, Any] = {}
        if tools:
            tool_schemas = [{"type": "function", "function": t.spec.as_schema()} for t in tools]
            tool_map = {t.spec.name: t for t in tools}

        response_format = None
        # OpenAI structured outputs require an object schema. If primitive, wrap.
        wrapped_primitive = False
        if output_schema and isinstance(output_schema, dict):
            schema = output_schema
            if schema.get("type") != "object":
                schema = {
                    "type": "object",
                    "properties": {"value": output_schema},
                    "required": ["value"],
                }
                wrapped_primitive = True
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "alloy_output", "schema": schema},
            }

        tool_turns = 0
        while True:
            is_gpt5 = bool(config.model and "gpt-5" in config.model)
            kwargs: dict[str, object] = {
                "model": config.model if config.model is not None else "",
                "messages": messages,
            }
            if tool_schemas is not None:
                kwargs["tools"] = tool_schemas
                kwargs["tool_choice"] = "auto"
            if (config.temperature is not None) and not is_gpt5:
                kwargs["temperature"] = config.temperature
            if config.max_tokens is not None:
                # Some newer models require max_completion_tokens instead of max_tokens
                use_completion_tokens = False
                m = (config.model or "").lower()
                if "gpt-5" in m or m.startswith("o1") or m.startswith("o3"):
                    use_completion_tokens = True
                kwargs["max_completion_tokens" if use_completion_tokens else "max_tokens"] = (
                    config.max_tokens
                )
            if response_format is not None:
                kwargs["response_format"] = response_format
            resp = client.chat.completions.create(**kwargs)

            choice = resp.choices[0]
            msg = choice.message
            tool_calls = getattr(msg, "tool_calls", None)

            if tool_calls:
                tool_turns += 1
                limit = config.max_tool_turns or 2
                if tool_turns > limit:
                    # Safety: avoid long loops; return current assistant content
                    return msg.content or ""
                # Append assistant message that requested tool calls first
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [tc for tc in tool_calls],
                    }
                )
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
                        try:
                            result = tool(**parsed) if isinstance(parsed, dict) else tool(parsed)
                            try:
                                content = json.dumps(result)
                            except Exception:
                                content = str(result)
                        except Exception as _tool_exc:
                            content = json.dumps({"type": "tool_error", "error": str(_tool_exc)})

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": name,
                            "content": content,
                        }
                    )
                continue

            content = msg.content or ""
            if response_format is not None and wrapped_primitive and content:
                # Try to extract {"value": ...} for primitives
                try:
                    import json as _json

                    data = _json.loads(content)
                    if isinstance(data, dict) and "value" in data:
                        return str(data["value"])  # let parse_output coerce type
                except Exception:
                    pass
            return content

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        try:
            from openai import OpenAI
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        if tools:
            raise ConfigurationError("Streaming with tools is not supported yet")

        client: Any = OpenAI()
        messages: list[dict[str, Any]] = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        is_gpt5 = bool(config.model and "gpt-5" in config.model)
        kwargs: dict[str, object] = {
            "model": config.model if config.model is not None else "",
            "messages": messages,
            "stream": True,
        }
        if (config.temperature is not None) and not is_gpt5:
            kwargs["temperature"] = config.temperature
        if config.max_tokens is not None:
            m = (config.model or "").lower()
            use_completion_tokens = ("gpt-5" in m) or m.startswith("o1") or m.startswith("o3")
            kwargs["max_completion_tokens" if use_completion_tokens else "max_tokens"] = (
                config.max_tokens
            )
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
            from openai import AsyncOpenAI
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        client: Any = AsyncOpenAI()
        messages: list[dict[str, Any]] = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        tool_schemas = None
        tool_map: dict[str, Any] = {}
        if tools:
            tool_schemas = [{"type": "function", "function": t.spec.as_schema()} for t in tools]
            tool_map = {t.spec.name: t for t in tools}

        response_format = None
        wrapped_primitive = False
        if output_schema and isinstance(output_schema, dict):
            schema = output_schema
            if schema.get("type") != "object":
                schema = {
                    "type": "object",
                    "properties": {"value": output_schema},
                    "required": ["value"],
                }
                wrapped_primitive = True
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "alloy_output", "schema": schema},
            }

        tool_turns = 0
        while True:
            is_gpt5 = bool(config.model and "gpt-5" in config.model)
            kwargs: dict[str, object] = {
                "model": config.model if config.model is not None else "",
                "messages": messages,
            }
            if tool_schemas is not None:
                kwargs["tools"] = tool_schemas
                kwargs["tool_choice"] = "auto"
            if (config.temperature is not None) and not is_gpt5:
                kwargs["temperature"] = config.temperature
            if config.max_tokens is not None:
                m = (config.model or "").lower()
                use_completion_tokens = ("gpt-5" in m) or m.startswith("o1") or m.startswith("o3")
                kwargs["max_completion_tokens" if use_completion_tokens else "max_tokens"] = (
                    config.max_tokens
                )
            if response_format is not None:
                kwargs["response_format"] = response_format
            resp = await client.chat.completions.create(**kwargs)
            choice = resp.choices[0]
            msg = choice.message
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                tool_turns += 1
                limit = config.max_tool_turns or 2
                if tool_turns > limit:
                    return msg.content or ""
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [tc for tc in tool_calls],
                    }
                )
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
                        try:
                            result = tool(**parsed) if isinstance(parsed, dict) else tool(parsed)
                            try:
                                content = json.dumps(result)
                            except Exception:
                                content = str(result)
                        except Exception as _tool_exc:
                            content = json.dumps({"type": "tool_error", "error": str(_tool_exc)})

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": name,
                            "content": content,
                        }
                    )
                continue
            content = msg.content or ""
            if response_format is not None and wrapped_primitive and content:
                try:
                    import json as _json

                    data = _json.loads(content)
                    if isinstance(data, dict) and "value" in data:
                        return str(data["value"])
                except Exception:
                    pass
            return content

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        try:
            from openai import AsyncOpenAI
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "OpenAI SDK not installed. Run `pip install openai>=1.0`."
            ) from e

        if tools:
            raise ConfigurationError("Streaming with tools is not supported yet")

        client: Any = AsyncOpenAI()
        messages: list[dict[str, Any]] = []
        if config.default_system:
            messages.append({"role": "system", "content": config.default_system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, object] = {
            "model": config.model if config.model is not None else "",
            "messages": messages,
            "stream": True,
        }
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        if config.max_tokens is not None:
            m = (config.model or "").lower()
            use_completion_tokens = ("gpt-5" in m) or m.startswith("o1") or m.startswith("o3")
            kwargs["max_completion_tokens" if use_completion_tokens else "max_tokens"] = (
                config.max_tokens
            )
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
