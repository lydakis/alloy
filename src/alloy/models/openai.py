from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any
import json

from ..config import Config
from ..errors import ConfigurationError, ToolError
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


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _extract_function_calls(resp: Any) -> list[dict[str, str]]:
    calls: list[dict[str, str]] = []
    items = _get(resp, "output", []) or []
    for item in items:
        if _get(item, "type") == "function_call":
            calls.append(
                {
                    "call_id": _get(item, "call_id", ""),
                    "name": _get(item, "name", ""),
                    "arguments": _get(item, "arguments", "{}"),
                }
            )
    return calls


def _output_as_str(resp: Any) -> str:
    parsed = _get(resp, "output_parsed", None)
    if parsed is not None:
        try:
            return json.dumps(parsed)
        except (TypeError, ValueError):
            return str(parsed)
    txt = _get(resp, "output_text", None)
    if isinstance(txt, str) and txt:
        return txt
    parts: list[str] = []
    for item in _get(resp, "output", []) or []:
        t = _get(item, "type")
        if t == "message":
            contents = _get(item, "content")
            if isinstance(contents, list):
                for c in contents:
                    if _get(c, "type") == "output_text":
                        val = _get(c, "text")
                        if isinstance(val, str):
                            parts.append(val)
        elif t == "output_text":
            val = _get(item, "text")
            if isinstance(val, str):
                parts.append(val)
    return "".join(parts)


class _LoopState:
    def __init__(
        self,
        *,
        prompt: str,
        config: Config,
        text_format: dict | None,
        tool_defs: list[dict] | None,
        tool_map: dict[str, Any],
    ) -> None:
        self.prompt = prompt
        self.config = config
        self.text_format = text_format
        self.tool_defs = tool_defs
        self.tool_map = tool_map
        self.turns = 0
        self.prev_id: str | None = None
        self.pending: list[dict[str, Any]] | None = None

    def build_kwargs(self) -> dict[str, object]:
        return _prepare_request_kwargs(
            self.prompt,
            config=self.config,
            text_format=self.text_format,
            tool_defs=self.tool_defs,
            pending=self.pending,
            prev_id=self.prev_id,
        )

    def after_response(self, resp: Any) -> tuple[bool, str]:
        self.prev_id = _get(resp, "id", self.prev_id)
        calls = _extract_function_calls(resp)
        if calls and self.tool_defs is not None:
            self.turns += 1
            limit = self.config.max_tool_turns or 2
            if self.turns > limit:
                return True, _output_as_str(resp)
            self.pending = _process_tool_calls(calls, self.tool_map)
            return False, ""
        return True, _output_as_str(resp)


def _is_temp_limited(model: str | None) -> bool:
    m = (model or "").lower()
    return ("gpt-5" in m) or m.startswith("o1") or m.startswith("o3")


def _prepare_request_kwargs(
    prompt: str,
    *,
    config: Config,
    text_format: dict | None,
    tool_defs: list[dict] | None,
    pending: list[dict[str, Any]] | None,
    prev_id: str | None,
) -> dict[str, object]:
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
    if (config.temperature is not None) and not _is_temp_limited(config.model):
        kwargs["temperature"] = config.temperature
    if config.max_tokens is not None:
        kwargs["max_output_tokens"] = config.max_tokens
    return kwargs


def _process_tool_calls(
    calls: list[dict[str, str]], tool_map: dict[str, Any]
) -> list[dict[str, str]]:
    outputs: list[dict[str, str]] = []
    for call in calls:
        name = call.get("name") or ""
        args_raw = call.get("arguments") or "{}"
        call_id = call.get("call_id") or ""
        tool = tool_map.get(name)
        if not tool:
            result_obj: Any = {"type": "tool_error", "error": f"Tool '{name}' not available."}
        else:
            try:
                parsed = json.loads(args_raw)
            except json.JSONDecodeError:
                parsed = {}
            try:
                result = tool(**parsed) if isinstance(parsed, dict) else tool(parsed)
                result_obj = result
            except Exception as exc:
                if isinstance(exc, ToolError):
                    result_obj = str(exc)
                else:
                    result_obj = {"type": "tool_error", "error": str(exc)}
        if isinstance(result_obj, str):
            result_json = result_obj
        else:
            try:
                result_json = json.dumps(result_obj)
            except (TypeError, ValueError):
                result_json = str(result_obj)
        outputs.append({"type": "function_call_output", "call_id": call_id, "output": result_json})
    return outputs


class OpenAIBackend(ModelBackend):
    """OpenAI backend using the Responses API.

    Implements completion and streaming via `responses.create`/`responses.stream`,
    supports function tool-calls by looping with `previous_response_id`, and
    emits structured outputs using `text.format` with a JSON Schema when an
    `output_schema` is provided. Raises `ConfigurationError` if the SDK is
    unavailable.
    """

    def __init__(self) -> None:
        self._OpenAI: Any | None = None
        self._AsyncOpenAI: Any | None = None
        try:
            from openai import OpenAI as _OpenAIClient

            self._OpenAI = _OpenAIClient
        except Exception:
            pass
        try:
            from openai import AsyncOpenAI as _AsyncOpenAIClient

            self._AsyncOpenAI = _AsyncOpenAIClient
        except Exception:
            pass

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        if self._OpenAI is None:
            raise ConfigurationError("OpenAI SDK not installed. Run `pip install openai>=1.99.6`.")
        client: Any = self._OpenAI()
        tool_defs, tool_map = _build_tools(tools)
        text_format = _build_text_format(output_schema)
        state = _LoopState(
            prompt=prompt,
            config=config,
            text_format=text_format,
            tool_defs=tool_defs,
            tool_map=tool_map,
        )
        while True:
            resp = client.responses.create(**state.build_kwargs())
            done, out = state.after_response(resp)
            if done:
                return out

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        if self._OpenAI is None:
            raise ConfigurationError("OpenAI SDK not installed. Run `pip install openai>=1.99.6`.")

        if tools:
            raise ConfigurationError("Streaming with tools is not supported yet")

        client: Any = self._OpenAI()
        text_format = _build_text_format(output_schema)
        kwargs = _prepare_request_kwargs(
            prompt,
            config=config,
            text_format=text_format,
            tool_defs=None,
            pending=None,
            prev_id=None,
        )
        stream = client.responses.stream(**kwargs)

        def gen():
            with stream as s:
                for event in s:
                    et = _get(event, "type", "")
                    if et == "response.output_text.delta":
                        delta = _get(event, "delta", "") or ""
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
        if self._AsyncOpenAI is None:
            raise ConfigurationError("OpenAI SDK not installed. Run `pip install openai>=1.99.6`.")
        client: Any = self._AsyncOpenAI()
        tool_defs, tool_map = _build_tools(tools)
        text_format = _build_text_format(output_schema)
        state = _LoopState(
            prompt=prompt,
            config=config,
            text_format=text_format,
            tool_defs=tool_defs,
            tool_map=tool_map,
        )
        while True:
            resp = await client.responses.create(**state.build_kwargs())
            done, out = state.after_response(resp)
            if done:
                return out

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        if self._AsyncOpenAI is None:
            raise ConfigurationError("OpenAI SDK not installed. Run `pip install openai>=1.99.6`.")

        if tools:
            raise ConfigurationError("Streaming with tools is not supported yet")

        client: Any = self._AsyncOpenAI()
        text_format = _build_text_format(output_schema)
        kwargs = _prepare_request_kwargs(
            prompt,
            config=config,
            text_format=text_format,
            tool_defs=None,
            pending=None,
            prev_id=None,
        )
        stream_ctx = client.responses.stream(**kwargs)

        async def agen():
            async with stream_ctx as s:
                async for event in s:
                    et = _get(event, "type", "")
                    if et == "response.output_text.delta":
                        delta = _get(event, "delta", "") or ""
                        if delta:
                            yield delta
                    elif et == "error":
                        break

        return agen()
