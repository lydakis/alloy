from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any
import json

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
    """Anthropic Claude backend."""

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        try:
            import anthropic
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            ) from e

        client: Any = anthropic.Anthropic()
        system = config.default_system
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]

        tool_defs = None
        tool_map: dict[str, Any] = {}
        synthetic_submit_name = "__alloy_submit__"
        if tools:
            tool_defs = [
                {
                    "name": t.spec.name,
                    "description": t.spec.description,
                    "input_schema": (
                        t.spec.as_schema().get("parameters")
                        if hasattr(t, "spec")
                        else {"type": "object"}
                    ),
                }
                for t in tools
            ]
            tool_map = {t.spec.name: t for t in tools}
        # If a structured output schema is provided, add a synthetic submit tool
        if output_schema and isinstance(output_schema, dict):
            schema = output_schema
            if schema.get("type") != "object":
                schema = {
                    "type": "object",
                    "properties": {"value": output_schema},
                    "required": ["value"],
                }
            tool_defs = (tool_defs or []) + [
                {
                    "name": synthetic_submit_name,
                    "description": "Submit the final structured output matching the schema.",
                    "input_schema": schema,
                }
            ]

        # Assistant prefill to bias JSON structure
        if output_schema and isinstance(output_schema, dict):

            def _prefill_from_schema(s: dict) -> str:
                t = s.get("type")
                if t == "object":
                    return "{"
                # For primitives, we wrap as {"value": ...}
                return '{"value":'

            messages.append(
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": _prefill_from_schema(output_schema)}],
                }
            )

        turns = 0
        while True:
            kwargs: dict[str, Any] = {
                "model": config.model,
                "messages": messages,
                "max_tokens": config.max_tokens or 512,
            }
            if system:
                kwargs["system"] = system
            if config.temperature is not None:
                kwargs["temperature"] = config.temperature
            if tool_defs is not None:
                kwargs["tools"] = tool_defs
            resp = client.messages.create(**kwargs)
            content = getattr(resp, "content", []) or []
            # Look for any tool_use blocks
            tool_calls = [
                block
                for block in content
                if getattr(block, "type", None) == "tool_use"
                or (isinstance(block, dict) and block.get("type") == "tool_use")
            ]
            if tool_calls and tool_defs is not None:
                turns += 1
                limit = config.max_tool_turns or 2
                if turns > limit:
                    # Return whatever text we have so far
                    return _as_text_from_content(resp)
                messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )
                for tc in tool_calls:
                    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
                    args = tc.get("input") if isinstance(tc, dict) else getattr(tc, "input", {})
                    tuid = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", "")
                    # Synthetic submit tool: return the structured args immediately
                    if name == synthetic_submit_name:
                        try:
                            return json.dumps(args)
                        except Exception:
                            return str(args)
                    tool = tool_map.get(name or "")
                    result: Any
                    if not tool:
                        result = {"type": "tool_error", "error": f"Tool '{name}' not available"}
                    else:
                        try:
                            result = tool(**args) if isinstance(args, dict) else tool(args)
                        except Exception as e:
                            from ..errors import ToolError as _ToolError  # local import

                            if isinstance(e, _ToolError):
                                result = str(e)
                            else:
                                result = {"type": "tool_error", "error": str(e)}
                    if isinstance(result, str):
                        result_text = result
                    else:
                        try:
                            result_text = json.dumps(result)
                        except Exception:
                            result_text = str(result)
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tuid,
                                    "content": result_text,
                                }
                            ],
                        }
                    )
                continue
            return _as_text_from_content(resp)

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
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
            import anthropic
        except Exception as e:  # pragma: no cover
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            ) from e

        client: Any = anthropic.AsyncAnthropic()
        system = config.default_system
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
        tool_defs = None
        tool_map: dict[str, Any] = {}
        synthetic_submit_name = "__alloy_submit__"
        if tools:
            tool_defs = [
                {
                    "name": t.spec.name,
                    "description": t.spec.description,
                    "input_schema": (
                        t.spec.as_schema().get("parameters")
                        if hasattr(t, "spec")
                        else {"type": "object"}
                    ),
                }
                for t in tools
            ]
            tool_map = {t.spec.name: t for t in tools}
        if output_schema and isinstance(output_schema, dict):
            schema = output_schema
            if schema.get("type") != "object":
                schema = {
                    "type": "object",
                    "properties": {"value": output_schema},
                    "required": ["value"],
                }
            tool_defs = (tool_defs or []) + [
                {
                    "name": synthetic_submit_name,
                    "description": "Submit the final structured output matching the schema.",
                    "input_schema": schema,
                }
            ]

        # Do not pass response_format; rely on prompt shaping and parsing.
        # Optional: assistant prefill to bias JSON structure
        if output_schema and isinstance(output_schema, dict):

            def _prefill_from_schema(s: dict) -> str:
                t = s.get("type")
                if t == "object":
                    return "{"
                return '{"value":'

            messages.append(
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": _prefill_from_schema(output_schema)}],
                }
            )

        turns = 0
        while True:
            kwargs: dict[str, Any] = {
                "model": config.model,
                "messages": messages,
                "max_tokens": config.max_tokens or 512,
            }
            if system:
                kwargs["system"] = system
            if config.temperature is not None:
                kwargs["temperature"] = config.temperature
            if tool_defs is not None:
                kwargs["tools"] = tool_defs
            resp = await client.messages.create(**kwargs)
            content = getattr(resp, "content", []) or []
            tool_calls = [
                block
                for block in content
                if getattr(block, "type", None) == "tool_use"
                or (isinstance(block, dict) and block.get("type") == "tool_use")
            ]
            if tool_calls and tool_defs is not None:
                turns += 1
                limit = config.max_tool_turns or 2
                if turns > limit:
                    return _as_text_from_content(resp)
                messages.append({"role": "assistant", "content": content})
                for tc in tool_calls:
                    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
                    args = tc.get("input") if isinstance(tc, dict) else getattr(tc, "input", {})
                    tuid = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", "")
                    if name == synthetic_submit_name:
                        try:
                            return json.dumps(args)
                        except Exception:
                            return str(args)
                    tool = tool_map.get(name or "")
                    if not tool:
                        result = {"type": "tool_error", "error": f"Tool '{name}' not available"}
                    else:
                        try:
                            result = tool(**args) if isinstance(args, dict) else tool(args)
                        except Exception as e:
                            result = {"type": "tool_error", "error": str(e)}
                    try:
                        result_text = json.dumps(result)
                    except Exception:
                        result_text = str(result)
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tuid,
                                    "content": result_text,
                                }
                            ],
                        }
                    )
                continue
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
