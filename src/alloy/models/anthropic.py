from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any
import json
import concurrent.futures

from ..config import Config
from ..errors import ConfigurationError, ToolLoopLimitExceeded, ToolError
from .base import ModelBackend


def _as_text_from_content(content: Any) -> str:
    try:
        parts = []
        for block in getattr(content, "content", []) or []:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            else:
                t = getattr(block, "type", None)
                if t == "text":
                    parts.append(getattr(block, "text", ""))
        return "".join(parts) or getattr(content, "text", "") or ""
    except Exception:
        return ""


_ANTHROPIC_REQUIRED_MAX_TOKENS = 2048  # Anthropic requires max_tokens; use this if unspecified


class _LoopState:
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
        self.config = config
        self.system = system
        self.tool_defs = tool_defs
        self.tool_map = tool_map
        self.turns = 0
        self.prefill = prefill
        self.messages: list[dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
        self.exceeded_tool_limit: bool = False
        if prefill:
            self.messages.append(
                {"role": "assistant", "content": [{"type": "text", "text": prefill}]}
            )

    def build_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": self.messages,
        }
        # Anthropic API requires max_tokens on every call. If not provided in
        # Config, use a conservative fallback. Prefer setting ALLOY_MAX_TOKENS.
        mt = (
            int(self.config.max_tokens)
            if self.config.max_tokens is not None
            else _ANTHROPIC_REQUIRED_MAX_TOKENS
        )
        kwargs["max_tokens"] = mt
        if self.system:
            kwargs["system"] = self.system
        if self.config.temperature is not None:
            kwargs["temperature"] = self.config.temperature
        if self.tool_defs is not None:
            kwargs["tools"] = self.tool_defs
        return kwargs

    def _collect_tool_calls(self, content: Any) -> list[dict[str, Any]]:
        tool_calls: list[dict[str, Any]] = []
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

    def after_response(self, resp: Any) -> tuple[bool, str]:
        content = getattr(resp, "content", []) or []
        tool_calls = self._collect_tool_calls(content)
        if tool_calls and self.tool_defs is not None:
            self.turns += 1
            limit = self.config.max_tool_turns
            if isinstance(limit, int) and limit >= 0 and self.turns > limit:
                self.exceeded_tool_limit = True
                return True, _as_text_from_content(resp)
            self.messages.append({"role": "assistant", "content": content})

            def _exec(tc: dict[str, Any]) -> tuple[str, str, bool]:
                name = str(tc.get("name") or "")
                args = tc.get("input")
                if not isinstance(args, dict):
                    args = {}
                tuid = str(tc.get("id") or "")
                tool = self.tool_map.get(name)
                is_error = False
                if not tool:
                    is_error = True
                    result_obj: Any = f"Tool '{name}' not available"
                else:
                    try:
                        result_obj = tool(**args)
                    except Exception as e:
                        is_error = True
                        if isinstance(e, ToolError):
                            result_obj = str(e)
                        else:
                            result_obj = f"{type(e).__name__}: {str(e)}"
                if isinstance(result_obj, str):
                    result_text = result_obj
                else:
                    try:
                        result_text = json.dumps(result_obj)
                    except Exception:
                        result_text = str(result_obj)
                return tuid, result_text, is_error

            if len(tool_calls) <= 1:
                results = [_exec(tool_calls[0])]
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(tool_calls)) as ex:
                    futures = [ex.submit(_exec, tc) for tc in tool_calls]
                    results = [f.result() for f in futures]

            blocks: list[dict[str, Any]] = []
            for tuid, text, is_error in results:
                block: dict[str, Any] = {
                    "type": "tool_result",
                    "tool_use_id": tuid,
                    "content": text,
                }
                if is_error:
                    block["is_error"] = True
                blocks.append(block)
            self.messages.append({"role": "user", "content": blocks})
            if self.prefill:
                self.messages.append(
                    {"role": "assistant", "content": [{"type": "text", "text": self.prefill}]}
                )
            return False, ""
        text_out = _as_text_from_content(resp)
        if self.prefill:
            return True, f"{self.prefill}{text_out}"
        return True, text_out


class AnthropicBackend(ModelBackend):
    """Anthropic Claude backend."""

    def __init__(self) -> None:
        self._Anthropic: Any | None = None
        self._AsyncAnthropic: Any | None = None
        try:
            import anthropic as _anthropic

            self._Anthropic = getattr(_anthropic, "Anthropic", None)
            self._AsyncAnthropic = getattr(_anthropic, "AsyncAnthropic", None)
        except Exception:
            pass

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
        if self._Anthropic is None:
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            )

        client: Any = self._Anthropic()
        system = config.default_system

        tool_defs, tool_map, prefill, system_hint = self._prepare_conversation(tools, output_schema)

        sys_str = system
        if isinstance(system_hint, str) and system_hint:
            sys_str = f"{system}\n\n{system_hint}" if system else system_hint

        state = _LoopState(
            prompt=prompt,
            config=config,
            system=sys_str,
            tool_defs=tool_defs,
            tool_map=tool_map,
            prefill=prefill,
        )
        return self._run_loop_sync(client, state, config)

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
        if self._Anthropic is None:
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            )
        client: Any = self._Anthropic()
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
        if self._AsyncAnthropic is None:
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            )

        client: Any = self._AsyncAnthropic()
        system = config.default_system
        tool_defs, tool_map, prefill, system_hint = self._prepare_conversation(tools, output_schema)

        sys_str = system
        if isinstance(system_hint, str) and system_hint:
            sys_str = f"{system}\n\n{system_hint}" if system else system_hint

        state = _LoopState(
            prompt=prompt,
            config=config,
            system=sys_str,
            tool_defs=tool_defs,
            tool_map=tool_map,
            prefill=prefill,
        )
        return await self._run_loop_async(client, state, config)

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
        if self._AsyncAnthropic is None:
            raise ConfigurationError(
                "Anthropic SDK not installed. Run `pip install alloy[anthropic]`."
            )
        client: Any = self._AsyncAnthropic()
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

    def _apply_tool_choice(
        self, kwargs: dict[str, Any], tools_present: bool, extra: Any, tool_turns: int
    ) -> None:
        if not tools_present:
            kwargs.pop("tool_choice", None)
            return
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

    def _finalize_json_only_sync(self, client: Any, state: _LoopState) -> str | None:
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
        kwargs2 = state.build_kwargs()
        kwargs2.pop("tools", None)
        kwargs2.pop("tool_choice", None)
        resp2 = client.messages.create(**kwargs2)
        out2 = _as_text_from_content(resp2)
        return f"{state.prefill}{out2}" if out2 else None

    async def _finalize_json_only_async(self, client: Any, state: _LoopState) -> str | None:
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
        kwargs2 = state.build_kwargs()
        kwargs2.pop("tools", None)
        kwargs2.pop("tool_choice", None)
        resp2 = await client.messages.create(**kwargs2)
        out2 = _as_text_from_content(resp2)
        return f"{state.prefill}{out2}" if out2 else None

    def _run_loop_sync(self, client: Any, state: _LoopState, config: Config) -> str:
        while True:
            kwargs = state.build_kwargs()
            extra = getattr(config, "extra", {}) or {}
            self._apply_tool_choice(kwargs, state.tool_defs is not None, extra, state.turns)
            resp = client.messages.create(**kwargs)
            done, out = state.after_response(resp)
            if done:
                if state.exceeded_tool_limit:
                    lim = state.config.max_tool_turns
                    raise ToolLoopLimitExceeded(
                        f"Exceeded tool-call turn limit (max_tool_turns={lim}). No final answer produced."
                    )
                if state.prefill and state.tool_defs is not None:
                    out2 = self._finalize_json_only_sync(client, state)
                    if isinstance(out2, str) and out2:
                        return out2
                return out

    async def _run_loop_async(self, client: Any, state: _LoopState, config: Config) -> str:
        while True:
            kwargs = state.build_kwargs()
            extra = getattr(config, "extra", {}) or {}
            self._apply_tool_choice(kwargs, state.tool_defs is not None, extra, state.turns)
            resp = await client.messages.create(**kwargs)
            done, out = state.after_response(resp)
            if done:
                if state.exceeded_tool_limit:
                    lim = state.config.max_tool_turns
                    raise ToolLoopLimitExceeded(
                        f"Exceeded tool-call turn limit (max_tool_turns={lim}). No final answer produced."
                    )
                if state.prefill and state.tool_defs is not None:
                    out2 = await self._finalize_json_only_async(client, state)
                    if isinstance(out2, str) and out2:
                        return out2
                return out

    def _prepare_stream_kwargs(self, prompt: str, config: Config) -> dict[str, Any]:
        state = _LoopState(
            prompt=prompt,
            config=config,
            system=config.default_system,
            tool_defs=None,
            tool_map={},
            prefill=None,
        )
        kwargs = state.build_kwargs()
        kwargs.pop("tools", None)
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
