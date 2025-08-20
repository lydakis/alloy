from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError
from .base import ModelBackend


def _build_text_format(output_schema: dict | None) -> dict | None:
    if not output_schema or not isinstance(output_schema, dict):
        return None
    schema = dict(output_schema)
    if schema.get("type") != "object":
        schema = {
            "type": "object",
            "properties": {"value": output_schema},
            "required": ["value"],
        }
    if "additionalProperties" not in schema:
        schema["additionalProperties"] = False
    return {"type": "json_schema", "name": "alloy_output", "schema": schema, "strict": True}


def _build_tools(tools: list | None) -> tuple[list[dict] | None, dict[str, Any]]:
    if not tools:
        return None, {}
    tool_defs: list[dict] = []
    tool_map: dict[str, Any] = {}
    for t in tools:
        spec = t.spec.as_schema()
        params = spec.get("parameters") if isinstance(spec, dict) else None
        if not isinstance(params, dict):
            params = {"type": "object"}
        tool_defs.append(
            {
                "type": "function",
                "name": t.spec.name,
                "description": t.spec.description,
                "parameters": params,
            }
        )
        tool_map[t.spec.name] = t
    return tool_defs, tool_map


def _extract_function_calls(resp: Any) -> list[dict[str, str]]:
    calls: list[dict[str, str]] = []
    try:
        for it in getattr(resp, "output", []) or []:
            item = it
            t = getattr(item, "type", None) if not isinstance(item, dict) else item.get("type")
            if t == "function_call":
                calls.append(
                    {
                        "call_id": (
                            getattr(item, "call_id", "")
                            if not isinstance(item, dict)
                            else item.get("call_id", "")
                        ),
                        "name": (
                            getattr(item, "name", "")
                            if not isinstance(item, dict)
                            else item.get("name", "")
                        ),
                        "arguments": (
                            getattr(item, "arguments", "{}")
                            if not isinstance(item, dict)
                            else item.get("arguments", "{}")
                        ),
                    }
                )
    except Exception:
        pass
    return calls


def _output_as_str(resp: Any) -> str:
    try:
        parsed = getattr(resp, "output_parsed", None)
        if parsed is not None:
            import json as _json

            try:
                return _json.dumps(parsed)
            except Exception:
                return str(parsed)
    except Exception:
        pass
    try:
        txt = getattr(resp, "output_text", None)
        if isinstance(txt, str) and txt:
            return txt
    except Exception:
        pass
    try:
        parts: list[str] = []
        for it in getattr(resp, "output", []) or []:
            item = it
            t = getattr(item, "type", None) if not isinstance(item, dict) else item.get("type")
            if t == "message":
                contents = (
                    getattr(item, "content", None)
                    if not isinstance(item, dict)
                    else item.get("content")
                )
                if isinstance(contents, list):
                    for c in contents:
                        ct = getattr(c, "type", None) if not isinstance(c, dict) else c.get("type")
                        if ct == "output_text":
                            val = (
                                getattr(c, "text", None)
                                if not isinstance(c, dict)
                                else c.get("text")
                            )
                            if isinstance(val, str):
                                parts.append(val)
            elif t == "output_text":
                val = (
                    getattr(item, "text", None) if not isinstance(item, dict) else item.get("text")
                )
                if isinstance(val, str):
                    parts.append(val)
        return "".join(parts)
    except Exception:
        return ""


class OpenAIBackend(ModelBackend):
    """OpenAI backend using the Responses API.

    Implements completion and streaming via `responses.create`/`responses.stream`,
    supports function tool-calls by looping with `previous_response_id`, and
    emits structured outputs using `text.format` with a JSON Schema when an
    `output_schema` is provided. Raises `ConfigurationError` if the SDK is
    unavailable.
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
                "OpenAI SDK not installed. Run `pip install openai>=1.99.6`."
            ) from e

        client: Any = OpenAI()
        tool_defs, tool_map = _build_tools(tools)
        text_format = _build_text_format(output_schema)

        is_gpt5 = bool(config.model and "gpt-5" in config.model)
        is_o_family = bool(
            (config.model or "").lower().startswith("o1")
            or (config.model or "").lower().startswith("o3")
        )

        turns = 0
        prev_id: str | None = None
        pending: list[dict[str, Any]] | None = None
        while True:
            kwargs: dict[str, object] = {"model": config.model or ""}
            if config.default_system:
                kwargs["instructions"] = str(config.default_system)
            if pending is None:
                kwargs["input"] = prompt
            else:
                kwargs["previous_response_id"] = prev_id or ""
                kwargs["input"] = pending
            if tool_defs is not None:
                kwargs["tools"] = tool_defs
                kwargs["tool_choice"] = "auto"
            if text_format is not None:
                kwargs["text"] = {"format": text_format}
            if (config.temperature is not None) and not (is_gpt5 or is_o_family):
                kwargs["temperature"] = config.temperature
            if config.max_tokens is not None:
                kwargs["max_output_tokens"] = config.max_tokens

            resp = client.responses.create(**kwargs)
            prev_id = getattr(resp, "id", None) or prev_id

            calls = _extract_function_calls(resp)
            if calls and tool_defs is not None:
                turns += 1
                limit = config.max_tool_turns or 2
                if turns > limit:
                    return _output_as_str(resp)
                import json as _json

                outputs: list[dict[str, str]] = []
                for call in calls:
                    name = call.get("name") or ""
                    args_raw = call.get("arguments") or "{}"
                    call_id = call.get("call_id") or ""
                    tool = tool_map.get(name)
                    if not tool:
                        result_obj: Any = {
                            "type": "tool_error",
                            "error": f"Tool '{name}' not available.",
                        }
                    else:
                        try:
                            parsed = _json.loads(args_raw)
                        except Exception:
                            parsed = {}
                        try:
                            result = tool(**parsed) if isinstance(parsed, dict) else tool(parsed)
                            result_obj = result
                        except Exception as exc:
                            from ..errors import ToolError as _ToolError  # local import

                            if isinstance(exc, _ToolError):
                                result_obj = str(exc)
                            else:
                                result_obj = {"type": "tool_error", "error": str(exc)}
                    if isinstance(result_obj, str):
                        result_json = result_obj
                    else:
                        try:
                            result_json = _json.dumps(result_obj)
                        except Exception:
                            result_json = str(result_obj)
                    outputs.append(
                        {"type": "function_call_output", "call_id": call_id, "output": result_json}
                    )
                pending = outputs
                continue

            return _output_as_str(resp)

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
                "OpenAI SDK not installed. Run `pip install openai>=1.99.6`."
            ) from e

        if tools:
            raise ConfigurationError("Streaming with tools is not supported yet")

        client: Any = OpenAI()
        text_format = _build_text_format(output_schema)

        is_gpt5 = bool(config.model and "gpt-5" in config.model)
        is_o_family = bool(
            (config.model or "").lower().startswith("o1")
            or (config.model or "").lower().startswith("o3")
        )

        kwargs: dict[str, object] = {"model": config.model or "", "input": prompt}
        if config.default_system:
            kwargs["instructions"] = str(config.default_system)
        if text_format is not None:
            kwargs["text"] = {"format": text_format}
        if (config.temperature is not None) and not (is_gpt5 or is_o_family):
            kwargs["temperature"] = config.temperature
        if config.max_tokens is not None:
            kwargs["max_output_tokens"] = config.max_tokens

        stream = client.responses.stream(**kwargs)

        def gen():
            with stream as s:
                for event in s:
                    et = getattr(event, "type", "")
                    if et == "response.output_text.delta":
                        delta = getattr(event, "delta", "") or ""
                        if delta:
                            yield delta
                    elif et == "error":
                        break

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
                "OpenAI SDK not installed. Run `pip install openai>=1.99.6`."
            ) from e

        client: Any = AsyncOpenAI()
        tool_defs, tool_map = _build_tools(tools)
        text_format = _build_text_format(output_schema)

        is_gpt5 = bool(config.model and "gpt-5" in config.model)
        is_o_family = bool(
            (config.model or "").lower().startswith("o1")
            or (config.model or "").lower().startswith("o3")
        )

        turns = 0
        prev_id: str | None = None
        pending: list[dict[str, Any]] | None = None
        while True:
            kwargs: dict[str, object] = {"model": config.model or ""}
            if config.default_system:
                kwargs["instructions"] = str(config.default_system)
            if pending is None:
                kwargs["input"] = prompt
            else:
                kwargs["previous_response_id"] = prev_id or ""
                kwargs["input"] = pending
            if tool_defs is not None:
                kwargs["tools"] = tool_defs
                kwargs["tool_choice"] = "auto"
            if text_format is not None:
                kwargs["text"] = {"format": text_format}
            if (config.temperature is not None) and not (is_gpt5 or is_o_family):
                kwargs["temperature"] = config.temperature
            if config.max_tokens is not None:
                kwargs["max_output_tokens"] = config.max_tokens

            resp = await client.responses.create(**kwargs)
            prev_id = getattr(resp, "id", None) or prev_id

            calls = _extract_function_calls(resp)
            if calls and tool_defs is not None:
                turns += 1
                limit = config.max_tool_turns or 2
                if turns > limit:
                    return _output_as_str(resp)
                import json as _json

                outputs: list[dict[str, str]] = []
                for call in calls:
                    name = call.get("name") or ""
                    args_raw = call.get("arguments") or "{}"
                    call_id = call.get("call_id") or ""
                    tool = tool_map.get(name)
                    if not tool:
                        result_obj: Any = {
                            "type": "tool_error",
                            "error": f"Tool '{name}' not available",
                        }
                    else:
                        try:
                            parsed = _json.loads(args_raw)
                        except Exception:
                            parsed = {}
                        try:
                            result = tool(**parsed) if isinstance(parsed, dict) else tool(parsed)
                            result_obj = result
                        except Exception as exc:
                            from ..errors import ToolError as _ToolError  # local import

                            if isinstance(exc, _ToolError):
                                result_obj = str(exc)
                            else:
                                result_obj = {"type": "tool_error", "error": str(exc)}
                    if isinstance(result_obj, str):
                        result_json = result_obj
                    else:
                        try:
                            result_json = _json.dumps(result_obj)
                        except Exception:
                            result_json = str(result_obj)
                    outputs.append(
                        {"type": "function_call_output", "call_id": call_id, "output": result_json}
                    )
                pending = outputs
                continue

            return _output_as_str(resp)

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
                "OpenAI SDK not installed. Run `pip install openai>=1.99.6`."
            ) from e

        if tools:
            raise ConfigurationError("Streaming with tools is not supported yet")

        client: Any = AsyncOpenAI()
        text_format = _build_text_format(output_schema)

        is_gpt5 = bool(config.model and "gpt-5" in config.model)
        is_o_family = bool(
            (config.model or "").lower().startswith("o1")
            or (config.model or "").lower().startswith("o3")
        )

        kwargs: dict[str, object] = {"model": config.model or "", "input": prompt}
        if config.default_system:
            kwargs["instructions"] = str(config.default_system)
        if text_format is not None:
            kwargs["text"] = {"format": text_format}
        if (config.temperature is not None) and not (is_gpt5 or is_o_family):
            kwargs["temperature"] = config.temperature
        if config.max_tokens is not None:
            kwargs["max_output_tokens"] = config.max_tokens

        stream_ctx = client.responses.stream(**kwargs)

        async def agen():
            async with stream_ctx as s:
                async for event in s:
                    et = getattr(event, "type", "")
                    if et == "response.output_text.delta":
                        delta = getattr(event, "delta", "") or ""
                        if delta:
                            yield delta
                    elif et == "error":
                        break

        return agen()
