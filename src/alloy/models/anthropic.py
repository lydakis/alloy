from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any
import json

from ..config import Config
from ..errors import (
    ConfigurationError,
)
from .base import ModelBackend, BaseLoopState, ToolCall, ToolResult

_ANTHROPIC_REQUIRED_MAX_TOKENS = 2048


def _extract_text_from_response(resp: Any) -> str:
    try:
        parts = []
        for block in getattr(resp, "content", []) or []:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            else:
                t = getattr(block, "type", None)
                if t == "text":
                    parts.append(getattr(block, "text", ""))
        return "".join(parts) or getattr(resp, "text", "") or ""
    except Exception:
        return ""


def _finalize_json_output(client: Any, state: "AnthropicLoopState") -> str | None:
    state.messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Continue and return only the final answer in the required JSON format, with no extra text.",
                }
            ],
        }
    )
    state.messages.append(
        {"role": "assistant", "content": [{"type": "text", "text": state.prefill}]}
    )
    kwargs2 = state._base_kwargs()
    kwargs2.pop("tools", None)
    kwargs2.pop("tool_choice", None)
    resp2 = client.messages.create(**kwargs2)
    out2 = _extract_text_from_response(resp2)
    return f"{state.prefill}{out2}" if out2 else None


async def _afinalize_json_output(client: Any, state: "AnthropicLoopState") -> str | None:
    state.messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Continue and return only the final answer in the required JSON format, with no extra text.",
                }
            ],
        }
    )
    state.messages.append(
        {"role": "assistant", "content": [{"type": "text", "text": state.prefill}]}
    )
    kwargs2 = state._base_kwargs()
    kwargs2.pop("tools", None)
    kwargs2.pop("tool_choice", None)
    resp2 = await client.messages.create(**kwargs2)
    out2 = _extract_text_from_response(resp2)
    return f"{state.prefill}{out2}" if out2 else None


def _extract_tool_calls(resp: Any) -> list[dict[str, Any]]:
    tool_calls: list[dict[str, Any]] = []
    content = getattr(resp, "content", []) or []
    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "tool_use":
                tool_calls.append(block)
        else:
            if getattr(block, "type", None) == "tool_use":
                tool_calls.append(
                    {
                        "type": "tool_use",
                        "id": getattr(block, "id", ""),
                        "name": getattr(block, "name", ""),
                        "input": getattr(block, "input", {}) or {},
                    }
                )
    return tool_calls


class AnthropicLoopState(BaseLoopState[Any]):
    def __init__(
        self,
        *,
        prompt: str,
        config: Config,
        system: str | None,
        tool_defs: list[dict[str, Any]] | None,
        tool_map: dict[str, Any],
        prefill: str | None,
    ) -> None:
        super().__init__(config, tool_map)
        self.system = system
        self.tool_defs = tool_defs
        self.prefill = prefill
        self.messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
        if prefill:
            self.messages.append(
                {"role": "assistant", "content": [{"type": "text", "text": prefill}]}
            )
        self._last_assistant_content: list[dict[str, Any]] | None = None

    def _apply_tool_choice(self, kwargs: dict[str, Any]) -> None:
        if self.tool_defs is None:
            kwargs.pop("tool_choice", None)
            return
        extra = getattr(self.config, "extra", {}) or {}
        choice: dict[str, Any] = {"type": "auto"}
        if isinstance(extra, dict):
            override = extra.get("anthropic_tool_choice")
            if isinstance(override, dict) and override.get("type") in {
                "auto",
                "any",
                "tool",
                "none",
            }:
                choice = dict(override)
            dptu = extra.get("anthropic_disable_parallel_tool_use")
            if isinstance(dptu, bool) and choice.get("type") in {"auto", "any", "tool"}:
                choice["disable_parallel_tool_use"] = dptu
        kwargs["tool_choice"] = choice

    def _base_kwargs(self) -> dict[str, Any]:
        mt = (
            int(self.config.max_tokens)
            if self.config.max_tokens is not None
            else _ANTHROPIC_REQUIRED_MAX_TOKENS
        )
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": self.messages,
            "max_tokens": mt,
        }
        if self.system:
            kwargs["system"] = self.system
        if self.config.temperature is not None:
            kwargs["temperature"] = self.config.temperature
        if self.tool_defs is not None:
            kwargs["tools"] = self.tool_defs
        return kwargs

    def make_request(self, client: Any) -> Any:
        kwargs = self._base_kwargs()
        self._apply_tool_choice(kwargs)
        return client.messages.create(**kwargs)

    async def amake_request(self, client: Any) -> Any:
        kwargs = self._base_kwargs()
        self._apply_tool_choice(kwargs)
        return await client.messages.create(**kwargs)

    def extract_text(self, response: Any) -> str:
        txt = _extract_text_from_response(response)
        return f"{self.prefill}{txt}" if self.prefill and isinstance(txt, str) else txt

    def extract_tool_calls(self, response: Any) -> list[ToolCall] | None:
        self._last_assistant_content = getattr(response, "content", None) or []
        calls_raw = _extract_tool_calls(response)
        out: list[ToolCall] = []
        for c in calls_raw:
            name = str(c.get("name") or "")
            args = c.get("input")
            if not isinstance(args, dict):
                args = {}
            out.append(ToolCall(id=str(c.get("id") or ""), name=name, args=args))
        return out

    def add_tool_results(self, calls: list[ToolCall], results: list[ToolResult]) -> None:
        content = self._last_assistant_content
        if content:
            self.messages.append({"role": "assistant", "content": content})
        else:
            blocks = [
                {"type": "tool_use", "id": c.id or "", "name": c.name, "input": c.args}
                for c in calls
            ]
            self.messages.append({"role": "assistant", "content": blocks})
        blocks_out: list[dict[str, Any]] = []
        for call, res in zip(calls, results):
            payload = res.value if res.ok else res.error
            if isinstance(payload, str):
                result_text = payload
            else:
                try:
                    result_text = json.dumps(payload)
                except Exception:
                    result_text = str(payload)
            block: dict[str, Any] = {
                "type": "tool_result",
                "tool_use_id": str(call.id or ""),
                "content": result_text,
            }
            if not res.ok:
                block["is_error"] = True
            blocks_out.append(block)
        self.messages.append({"role": "user", "content": blocks_out})
        if self.prefill:
            self.messages.append(
                {"role": "assistant", "content": [{"type": "text", "text": self.prefill}]}
            )


class AnthropicBackend(ModelBackend):
    """Anthropic Claude backend."""

    def __init__(self) -> None:
        self._Anthropic: Any | None = None
        self._AsyncAnthropic: Any | None = None
        self._client_sync: Any | None = None
        self._client_async: Any | None = None
        try:
            import anthropic as _anthropic

            self._Anthropic = getattr(_anthropic, "Anthropic", None)
            self._AsyncAnthropic = getattr(_anthropic, "AsyncAnthropic", None)
        except Exception:
            pass

    def _get_sync_client(self) -> Any:
        if self._Anthropic is None:
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            )
        if self._client_sync is None:
            self._client_sync = self._Anthropic()
        return self._client_sync

    def _get_async_client(self) -> Any:
        if self._AsyncAnthropic is None:
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            )
        if self._client_async is None:
            self._client_async = self._AsyncAnthropic()
        return self._client_async

    def _prepare_conversation(
        self, tools: list | None, output_schema: dict | None
    ) -> tuple[list[dict[str, Any]] | None, dict[str, Any], str | None, str | None]:
        tool_defs: list[dict[str, Any]] | None = None
        tool_map: dict[str, Any] = {}
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

        prefill: str | None = None
        system_hint: str | None = None
        if output_schema and isinstance(output_schema, dict):

            def _prefill_from_schema(s: dict) -> str:
                t = s.get("type")
                if t == "object":
                    return "{"
                return '{"value":'

            t = output_schema.get("type")
            if t == "object":
                prefill = _prefill_from_schema(output_schema)
                props = (
                    output_schema.get("properties", {})
                    if isinstance(output_schema.get("properties"), dict)
                    else {}
                )
                keys = ", ".join(sorted(props.keys()))
                system_hint = (
                    "Return only a JSON object that exactly matches the required schema. "
                    f"Use these keys: {keys}. Use numbers for numeric fields without symbols. No extra text."
                )
            elif t in ("number", "integer", "boolean"):
                prefill = _prefill_from_schema(output_schema)
                system_hint = (
                    'Return only a JSON object of the form {"value": <value>} where <value> is the required type. '
                    "No extra text before or after the JSON."
                )
            else:
                prefill = None
                system_hint = None

        return tool_defs, tool_map, prefill, system_hint

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        client: Any = self._get_sync_client()
        system = config.default_system

        tool_defs, tool_map, prefill, system_hint = self._prepare_conversation(tools, output_schema)

        sys_str = system
        if isinstance(system_hint, str) and system_hint:
            sys_str = f"{system}\n\n{system_hint}" if system else system_hint

        state = AnthropicLoopState(
            prompt=prompt,
            config=config,
            system=sys_str,
            tool_defs=tool_defs,
            tool_map=tool_map,
            prefill=prefill,
        )
        out = self.run_tool_loop(client, state)
        if (
            state.prefill
            and state.tool_defs is not None
            and bool(config.auto_finalize_missing_output)
        ):
            out2 = _finalize_json_output(client, state)
            if isinstance(out2, str) and out2:
                return out2
        return out

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        if tools or output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        client: Any = self._get_sync_client()
        kwargs = self._prepare_stream_kwargs(prompt, config)
        stream_ctx = client.messages.stream(**kwargs)

        def gen():
            with stream_ctx as s:
                text_stream = getattr(s, "text_stream", None)
                if text_stream is not None:
                    for delta in text_stream:
                        if isinstance(delta, str) and delta:
                            yield delta
                    return
                for event in s:
                    text = self._parse_stream_event(event)
                    if isinstance(text, str) and text:
                        yield text

        return gen()

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        client: Any = self._get_async_client()
        system = config.default_system
        tool_defs, tool_map, prefill, system_hint = self._prepare_conversation(tools, output_schema)

        sys_str = system
        if isinstance(system_hint, str) and system_hint:
            sys_str = f"{system}\n\n{system_hint}" if system else system_hint

        state = AnthropicLoopState(
            prompt=prompt,
            config=config,
            system=sys_str,
            tool_defs=tool_defs,
            tool_map=tool_map,
            prefill=prefill,
        )
        out = await self.arun_tool_loop(client, state)
        if (
            state.prefill
            and state.tool_defs is not None
            and bool(config.auto_finalize_missing_output)
        ):
            out2 = await _afinalize_json_output(client, state)
            if isinstance(out2, str) and out2:
                return out2
        return out

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        if tools or output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        client: Any = self._get_async_client()
        kwargs = self._prepare_stream_kwargs(prompt, config)
        stream_ctx = client.messages.stream(**kwargs)

        async def agen():
            async with stream_ctx as s:
                text_stream = getattr(s, "text_stream", None)
                if text_stream is not None:
                    async for delta in text_stream:
                        if isinstance(delta, str) and delta:
                            yield delta
                    return
                async for event in s:
                    text = self._parse_stream_event(event)
                    if isinstance(text, str) and text:
                        yield text

        return agen()

    def _prepare_stream_kwargs(self, prompt: str, config: Config) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "max_tokens": (
                int(config.max_tokens)
                if config.max_tokens is not None
                else _ANTHROPIC_REQUIRED_MAX_TOKENS
            ),
        }
        if config.default_system:
            kwargs["system"] = str(config.default_system)
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        return kwargs

    def _parse_stream_event(self, event: Any) -> str | None:
        et = getattr(event, "type", None) or (event.get("type") if isinstance(event, dict) else "")
        if et == "content_block_delta":
            d = getattr(event, "delta", None) or (
                event.get("delta") if isinstance(event, dict) else None
            )
            text = getattr(d, "text", None) if d is not None else None
            if text is None and isinstance(d, dict):
                text = d.get("text")
            return text if isinstance(text, str) and text else None
        return None
