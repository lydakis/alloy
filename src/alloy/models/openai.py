from __future__ import annotations

from collections.abc import Iterable, AsyncIterable, Iterator, AsyncIterator
from typing import Any
import json

from ..config import Config
from ..errors import (
    ConfigurationError,
)
from .base import (
    ModelBackend,
    BaseLoopState,
    ToolCall,
    ToolResult,
    should_finalize_structured_output,
    serialize_tool_payload,
    build_tools_common,
    ensure_object_schema,
    STRICT_JSON_ONLY_MSG,
)


def _build_text_format(output_schema: dict | None) -> dict | None:
    if not output_schema or not isinstance(output_schema, dict):
        return None
    obj = ensure_object_schema(output_schema)
    if not isinstance(obj, dict):
        return None
    schema = dict(obj)
    if "additionalProperties" not in schema:
        schema["additionalProperties"] = False
    return {"type": "json_schema", "name": "alloy_output", "schema": schema, "strict": True}


def _build_tools(tools: list | None) -> tuple[list[dict] | None, dict[str, Any]]:
    def _fmt(name: str, description: str, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "function",
            "name": name,
            "description": description,
            "parameters": params,
        }

    return build_tools_common(tools, _fmt)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _extract_tool_calls(resp: Any) -> list[dict[str, str]]:
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


def _extract_text_from_response(resp: Any) -> str:
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


class OpenAILoopState(BaseLoopState[Any]):
    def __init__(
        self,
        *,
        prompt: str,
        config: Config,
        text_format: dict | None,
        tool_defs: list[dict] | None,
        tool_map: dict[str, Any],
    ) -> None:
        super().__init__(config, tool_map)
        self.prompt = prompt
        self.text_format = text_format
        self.tool_defs = tool_defs
        self.prev_id: str | None = None
        self.pending: list[dict[str, Any]] | None = None

    def _apply_tool_choice(self, kwargs: dict[str, Any]) -> None:
        if self.tool_defs is None:
            kwargs.pop("tool_choice", None)
            return
        extra = getattr(self.config, "extra", {}) or {}
        choice = None
        if isinstance(extra, dict):
            choice = extra.get("openai_tool_choice")
        if isinstance(choice, (str, dict)):
            kwargs["tool_choice"] = choice
        else:
            kwargs["tool_choice"] = "auto"

    def make_request(self, client: Any) -> Any:
        kwargs = _prepare_request_kwargs(
            self.prompt,
            config=self.config,
            text_format=self.text_format,
            tool_defs=self.tool_defs,
            pending=self.pending,
            prev_id=self.prev_id,
        )
        self._apply_tool_choice(kwargs)
        return client.responses.create(**kwargs)

    async def amake_request(self, client: Any) -> Any:
        kwargs = _prepare_request_kwargs(
            self.prompt,
            config=self.config,
            text_format=self.text_format,
            tool_defs=self.tool_defs,
            pending=self.pending,
            prev_id=self.prev_id,
        )
        self._apply_tool_choice(kwargs)
        return await client.responses.create(**kwargs)

    def extract_text(self, response: Any) -> str:
        self.prev_id = _get(response, "id", self.prev_id)
        return _extract_text_from_response(response)

    def extract_tool_calls(self, response: Any) -> list[ToolCall] | None:
        raw_calls = _extract_tool_calls(response)
        out: list[ToolCall] = []
        for c in raw_calls:
            raw = c.get("arguments") or "{}"
            try:
                args = json.loads(raw)
                if not isinstance(args, dict):
                    args = {}
            except Exception:
                args = {}
            out.append(ToolCall(id=c.get("call_id"), name=c.get("name", ""), args=args))
        return out

    def add_tool_results(self, calls: list[ToolCall], results: list[ToolResult]) -> None:
        pending: list[dict[str, Any]] = []
        for call, res in zip(calls, results):
            payload = res.value if res.ok else res.error
            out_json = serialize_tool_payload(payload)
            pending.append(
                {"type": "function_call_output", "call_id": call.id or "", "output": out_json}
            )
        self.pending = pending


def _is_temp_limited(model: str | None) -> bool:
    m = (model or "").lower()
    return ("gpt-5" in m) or m.startswith("o1") or m.startswith("o3") or m.startswith("o4")


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
        kwargs["input"] = pending
    if prev_id:
        kwargs["previous_response_id"] = prev_id
    if tool_defs is not None:
        kwargs["tools"] = tool_defs
    if text_format is not None:
        kwargs["text"] = {"format": text_format}
    if config.temperature is not None and not _is_temp_limited(config.model):
        kwargs["temperature"] = config.temperature
    if config.max_tokens is not None:
        kwargs["max_output_tokens"] = config.max_tokens
    return kwargs


def _finalize_json_output(client: Any, state: OpenAILoopState) -> str:

    kwargs2 = _prepare_request_kwargs(
        STRICT_JSON_ONLY_MSG,
        config=state.config,
        text_format=state.text_format,
        tool_defs=None,
        pending=None,
        prev_id=state.prev_id,
    )
    resp2 = client.responses.create(**kwargs2)
    return _extract_text_from_response(resp2)


async def _afinalize_json_output(client: Any, state: OpenAILoopState) -> str:

    kwargs2 = _prepare_request_kwargs(
        STRICT_JSON_ONLY_MSG,
        config=state.config,
        text_format=state.text_format,
        tool_defs=None,
        pending=None,
        prev_id=state.prev_id,
    )
    resp2 = await client.responses.create(**kwargs2)
    return _extract_text_from_response(resp2)


class OpenAIBackend(ModelBackend):
    """OpenAI backend using the Responses API.

    Implements completion and streaming via `responses.create`/`responses.stream`,
    supports function tool-calls by looping with `previous_response_id`, and
    emits structured outputs using `text.format` with a JSON Schema when an
    `output_schema` is provided. Raises `ConfigurationError` if the SDK is
    unavailable.
    """

    supports_streaming_tools = True

    def __init__(self) -> None:
        self._OpenAI: Any | None = None
        self._AsyncOpenAI: Any | None = None
        self._client_sync: Any | None = None
        self._client_async: Any | None = None
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
        client: Any = self._get_sync_client()
        tool_defs, tool_map = _build_tools(tools)
        text_format = _build_text_format(output_schema)
        state = OpenAILoopState(
            prompt=prompt,
            config=config,
            text_format=text_format,
            tool_defs=tool_defs,
            tool_map=tool_map,
        )
        out = self.run_tool_loop(client, state)
        if (
            text_format
            and isinstance(output_schema, dict)
            and bool(config.auto_finalize_missing_output)
            and should_finalize_structured_output(out, output_schema)
        ):
            return _finalize_json_output(client, state)
        return out

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        _ = self._get_sync_client()
        if output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; structured outputs are not supported"
            )

        client: Any = self._client_sync

        # Fast path: no tools → existing plain text stream
        if not tools:
            kwargs = _prepare_request_kwargs(
                prompt,
                config=config,
                text_format=None,
                tool_defs=None,
                pending=None,
                prev_id=None,
            )
            stream = client.responses.stream(**kwargs)

            def gen_plain():
                with stream as s:
                    for event in s:
                        et = _get(event, "type", "")
                        if et == "response.output_text.delta":
                            delta = _get(event, "delta", "") or ""
                            if delta:
                                yield delta
                        elif et == "error":
                            break

            return gen_plain()

        tool_defs, tool_map = _build_tools(tools)
        state = OpenAILoopState(
            prompt=prompt,
            config=config,
            text_format=None,
            tool_defs=tool_defs,
            tool_map=tool_map,
        )

        def stream_step(loop_state: BaseLoopState[Any]) -> Iterator[str]:
            if not isinstance(loop_state, OpenAILoopState):
                raise TypeError("stream_step expects OpenAILoopState")
            calls_holder: dict[str, list[ToolCall]] = {"value": []}

            def iterator() -> Iterator[str]:
                pending_payload = loop_state.pending
                loop_state.pending = None
                kwargs = _prepare_request_kwargs(
                    prompt,
                    config=config,
                    text_format=None,
                    tool_defs=loop_state.tool_defs,
                    pending=pending_payload,
                    prev_id=loop_state.prev_id,
                )
                loop_state._apply_tool_choice(kwargs)
                stream_ctx = client.responses.stream(**kwargs)

                by_id: dict[str, dict[str, str]] = {}
                final_resp_obj: Any | None = None

                with stream_ctx as s:
                    for event in s:
                        et = _get(event, "type", "")
                        if et == "response.created":
                            rid = _get(event, "response")
                            rid = _get(rid, "id", _get(event, "id"))
                            if isinstance(rid, str) and rid:
                                loop_state.prev_id = rid
                        elif et == "response.output_text.delta":
                            delta = _get(event, "delta", "") or ""
                            if delta:
                                yield delta
                        elif et == "response.output_item.added":
                            item = _get(event, "item", {})
                            if _get(item, "type") == "function_call":
                                cid = str(_get(item, "id") or _get(item, "call_id") or "")
                                name = str(_get(item, "name") or "")
                                if cid and cid not in by_id:
                                    by_id[cid] = {"name": name, "args": ""}
                        elif et == "response.function_call_arguments.delta":
                            cid = str(_get(event, "id") or _get(event, "call_id") or "")
                            if cid:
                                piece = _get(event, "delta", "") or ""
                                rec = by_id.setdefault(cid, {"name": "", "args": ""})
                                if isinstance(piece, str):
                                    rec["args"] += piece
                        elif et in ("error", "response.error"):
                            break

                    final_resp = getattr(s, "get_final_response", None)
                    if callable(final_resp):
                        try:
                            final_resp_obj = final_resp()
                        except Exception:
                            final_resp_obj = None

                calls: list[ToolCall] = []
                if final_resp_obj is not None:
                    try:
                        text_val = loop_state.extract_text(final_resp_obj)
                        loop_state.last_response_text = text_val
                        parsed = loop_state.extract_tool_calls(final_resp_obj) or []
                        if parsed:
                            calls = parsed
                    except Exception:
                        calls = []

                if not calls and by_id:
                    for cid, rec in by_id.items():
                        raw = rec.get("args") or "{}"
                        try:
                            args = json.loads(raw)
                            if not isinstance(args, dict):
                                args = {}
                        except Exception:
                            args = {}
                        calls.append(ToolCall(id=cid or None, name=rec.get("name", ""), args=args))

                calls_holder["value"] = calls

            class _StreamWrapper(Iterator[str]):
                def __init__(self, gen: Iterator[str]):
                    self._gen = gen

                def __iter__(self) -> Iterator[str]:
                    return self

                def __next__(self) -> str:
                    return next(self._gen)

                def _alloy_get_tool_calls(self) -> list[ToolCall]:
                    return calls_holder.get("value", [])

            return _StreamWrapper(iterator())

        return self.run_stream_loop(state, stream_step)

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        client: Any = self._get_async_client()
        tool_defs, tool_map = _build_tools(tools)
        text_format = _build_text_format(output_schema)
        state = OpenAILoopState(
            prompt=prompt,
            config=config,
            text_format=text_format,
            tool_defs=tool_defs,
            tool_map=tool_map,
        )
        out = await self.arun_tool_loop(client, state)
        if (
            text_format
            and isinstance(output_schema, dict)
            and bool(config.auto_finalize_missing_output)
            and should_finalize_structured_output(out, output_schema)
        ):
            return await _afinalize_json_output(client, state)
        return out

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        _ = self._get_async_client()
        if output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; structured outputs are not supported"
            )

        client: Any = self._client_async

        if not tools:
            kwargs = _prepare_request_kwargs(
                prompt,
                config=config,
                text_format=None,
                tool_defs=None,
                pending=None,
                prev_id=None,
            )
            stream_ctx = client.responses.stream(**kwargs)

            async def agen_plain():
                async with stream_ctx as s:
                    async for event in s:
                        et = _get(event, "type", "")
                        if et == "response.output_text.delta":
                            delta = _get(event, "delta", "") or ""
                            if delta:
                                yield delta
                        elif et == "error":
                            break

            return agen_plain()

        tool_defs, tool_map = _build_tools(tools)
        state = OpenAILoopState(
            prompt=prompt,
            config=config,
            text_format=None,
            tool_defs=tool_defs,
            tool_map=tool_map,
        )

        def stream_step(loop_state: BaseLoopState[Any]) -> AsyncIterator[str]:
            if not isinstance(loop_state, OpenAILoopState):
                raise TypeError("stream_step expects OpenAILoopState")
            calls_holder: dict[str, list[ToolCall]] = {"value": []}

            async def iterator() -> AsyncIterator[str]:
                pending_payload = loop_state.pending
                loop_state.pending = None
                kwargs = _prepare_request_kwargs(
                    prompt,
                    config=config,
                    text_format=None,
                    tool_defs=loop_state.tool_defs,
                    pending=pending_payload,
                    prev_id=loop_state.prev_id,
                )
                loop_state._apply_tool_choice(kwargs)
                stream_ctx = client.responses.stream(**kwargs)

                by_id: dict[str, dict[str, str]] = {}
                final_resp_obj: Any | None = None

                async with stream_ctx as s:
                    async for event in s:
                        et = _get(event, "type", "")
                        if et == "response.created":
                            rid = _get(event, "response")
                            rid = _get(rid, "id", _get(event, "id"))
                            if isinstance(rid, str) and rid:
                                loop_state.prev_id = rid
                        elif et == "response.output_text.delta":
                            delta = _get(event, "delta", "") or ""
                            if delta:
                                yield delta
                        elif et == "response.output_item.added":
                            item = _get(event, "item", {})
                            if _get(item, "type") == "function_call":
                                cid = str(_get(item, "id") or _get(item, "call_id") or "")
                                name = str(_get(item, "name") or "")
                                if cid and cid not in by_id:
                                    by_id[cid] = {"name": name, "args": ""}
                        elif et == "response.function_call_arguments.delta":
                            cid = str(_get(event, "id") or _get(event, "call_id") or "")
                            if cid:
                                piece = _get(event, "delta", "") or ""
                                rec = by_id.setdefault(cid, {"name": "", "args": ""})
                                if isinstance(piece, str):
                                    rec["args"] += piece
                        elif et in ("error", "response.error"):
                            break

                    final_resp = getattr(s, "get_final_response", None)
                    if callable(final_resp):
                        try:
                            final_resp_obj = await final_resp()
                        except Exception:
                            final_resp_obj = None

                calls: list[ToolCall] = []
                if final_resp_obj is not None:
                    try:
                        text_val = loop_state.extract_text(final_resp_obj)
                        loop_state.last_response_text = text_val
                        parsed = loop_state.extract_tool_calls(final_resp_obj) or []
                        if parsed:
                            calls = parsed
                    except Exception:
                        calls = []

                if not calls and by_id:
                    for cid, rec in by_id.items():
                        raw = rec.get("args") or "{}"
                        try:
                            args = json.loads(raw)
                            if not isinstance(args, dict):
                                args = {}
                        except Exception:
                            args = {}
                        calls.append(ToolCall(id=cid or None, name=rec.get("name", ""), args=args))

                calls_holder["value"] = calls

            class _AsyncStreamWrapper(AsyncIterator[str]):
                def __init__(self, agen: AsyncIterator[str]):
                    self._aiter = agen

                def __aiter__(self) -> AsyncIterator[str]:
                    return self

                async def __anext__(self) -> str:
                    return await self._aiter.__anext__()

                def _alloy_get_tool_calls(self) -> list[ToolCall]:
                    return calls_holder.get("value", [])

            return _AsyncStreamWrapper(iterator())

        return await self.arun_stream_loop(state, stream_step)

    def _get_sync_client(self) -> Any:
        if self._OpenAI is None:
            raise ConfigurationError("OpenAI SDK not installed. Run `pip install openai>=1.99.6`.")
        if self._client_sync is None:
            self._client_sync = self._OpenAI()
        return self._client_sync

    def _get_async_client(self) -> Any:
        if self._AsyncOpenAI is None:
            raise ConfigurationError("OpenAI SDK not installed. Run `pip install openai>=1.99.6`.")
        if self._client_async is None:
            self._client_async = self._AsyncOpenAI()
        return self._client_async
