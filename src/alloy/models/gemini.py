from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any, cast
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
    build_tools_common,
    ensure_object_schema,
)


def _prepare_config(config: Config, output_schema: dict | None) -> dict[str, object]:
    cfg: dict[str, object] = {}
    if config.default_system:
        cfg["system_instruction"] = str(config.default_system)
    if config.temperature is not None:
        cfg["temperature"] = float(config.temperature)
    if config.max_tokens is not None:
        cfg["max_output_tokens"] = int(config.max_tokens)
    if output_schema and isinstance(output_schema, dict):
        obj = ensure_object_schema(output_schema)
        if isinstance(obj, dict):
            cfg["response_mime_type"] = "application/json"
            cfg["response_json_schema"] = obj
    return cfg


def _schema_to_gemini(T: Any, s: dict[str, Any]) -> Any:
    t = (s.get("type") or "").lower()
    if t == "object":
        props = s.get("properties", {}) if isinstance(s.get("properties"), dict) else {}
        conv = {k: _schema_to_gemini(T, v) for k, v in props.items()}
        req = s.get("required", []) if isinstance(s.get("required"), list) else []
        return T.Schema(type="OBJECT", properties=conv, required=req)
    if t == "array":
        items_node = s.get("items")
        if not isinstance(items_node, dict):
            items_node = {"type": "STRING"}
        items = cast(dict[str, Any], items_node)
        return T.Schema(type="ARRAY", items=_schema_to_gemini(T, items))
    m = {
        "string": "STRING",
        "integer": "INTEGER",
        "number": "NUMBER",
        "boolean": "BOOLEAN",
    }.get(t, "STRING")
    return T.Schema(type=m)


def _finalize_json_output(
    T: Any, client: Any, model_name: str, messages: list[Any], cfg: dict[str, object]
) -> str:
    if T is None:
        raise ConfigurationError("Google GenAI SDK types not available")
    cfg2 = dict(cfg)
    cfg2.pop("tools", None)
    cfg2.pop("automatic_function_calling", None)
    from .base import STRICT_JSON_ONLY_MSG

    strict_msg = T.Content(
        role="user",
        parts=[T.Part.from_text(text=STRICT_JSON_ONLY_MSG)],
    )
    res = client.models.generate_content(
        model=model_name, contents=messages + [strict_msg], config=cfg2 or None
    )
    return _extract_text_from_response(res)


async def _afinalize_json_output(
    T: Any, client: Any, model_name: str, messages: list[Any], cfg: dict[str, object]
) -> str:
    if T is None:
        raise ConfigurationError("Google GenAI SDK types not available")
    cfg2 = dict(cfg)
    cfg2.pop("tools", None)
    cfg2.pop("automatic_function_calling", None)
    from .base import STRICT_JSON_ONLY_MSG

    strict_msg = T.Content(
        role="user",
        parts=[T.Part.from_text(text=STRICT_JSON_ONLY_MSG)],
    )
    res = await client.aio.models.generate_content(
        model=model_name, contents=messages + [strict_msg], config=cfg2 or None
    )
    return _extract_text_from_response(res)


class GeminiLoopState(BaseLoopState[Any]):
    def __init__(
        self,
        *,
        types_mod: Any,
        config: Config,
        tools: list[Any],
        cfg: dict[str, object],
        prompt: str,
    ) -> None:
        super().__init__(config, {})
        self.T = types_mod
        self.cfg = dict(cfg)
        decls, self.tool_map = _build_tools(tools, self.T)
        if decls:
            self.cfg["tools"] = [self.T.Tool(function_declarations=decls)]
        self.cfg["automatic_function_calling"] = self.T.AutomaticFunctionCallingConfig(disable=True)
        self.messages: list[Any] = [
            self.T.Content(role="user", parts=[self.T.Part.from_text(text=prompt)])
        ]
        self._last_assistant_content: Any | None = None

    def make_request(self, client: Any) -> Any:
        self._apply_tool_choice()
        return client.models.generate_content(
            model=self.config.model, contents=self.messages, config=self.cfg or None
        )

    async def amake_request(self, client: Any) -> Any:
        self._apply_tool_choice()
        return await client.aio.models.generate_content(
            model=self.config.model, contents=self.messages, config=self.cfg or None
        )

    def extract_text(self, response: Any) -> str:
        return _extract_text_from_response(response)

    def extract_tool_calls(self, response: Any) -> list[ToolCall] | None:
        self._last_assistant_content = None
        calls: list[ToolCall] = []
        fc_list = getattr(response, "function_calls", None)
        if fc_list:
            for fc in fc_list:
                name_val = getattr(fc, "name", None) or getattr(
                    getattr(fc, "function_call", None), "name", ""
                )
                args_val = getattr(getattr(fc, "function_call", None), "args", {})
                calls.append(ToolCall(id=None, name=str(name_val or ""), args=args_val or {}))
        if not calls:
            candidates = getattr(response, "candidates", None)
            if isinstance(candidates, list) and candidates:
                content_obj = getattr(candidates[0], "content", None)
                parts = getattr(content_obj, "parts", None)
                if content_obj is not None:
                    self._last_assistant_content = content_obj
                if isinstance(parts, list):
                    for p in parts:
                        fc = getattr(p, "function_call", None)
                        if fc is not None:
                            calls.append(
                                ToolCall(
                                    id=None,
                                    name=str(getattr(fc, "name", "") or ""),
                                    args=getattr(fc, "args", {}) or {},
                                )
                            )
        return calls

    def add_tool_results(self, calls: list[ToolCall], results: list[ToolResult]) -> None:
        if self._last_assistant_content is not None:
            self.messages.append(self._last_assistant_content)
        for call, res in zip(calls, results):
            payload = res.value if res.ok else res.error
            response_obj = payload if isinstance(payload, (dict, list)) else {"result": payload}
            resp_part = self.T.Part.from_function_response(
                name=(call.name or "unknown"), response=response_obj
            )
            self.messages.append(self.T.Content(role="tool", parts=[resp_part]))

    def _apply_tool_choice(self) -> None:
        T = self.T
        if T is None:
            return
        extra = getattr(self.config, "extra", {}) or {}
        try:
            tc = None
            allowed = None
            if isinstance(extra, dict):
                tc = extra.get("tool_choice") or extra.get("gemini_tool_choice")
                allowed = extra.get("allowed_tools") or extra.get("gemini_allowed_tools")
            mode_raw = None
            if isinstance(tc, dict):
                mode_raw = tc.get("type")
            elif isinstance(tc, str):
                mode_raw = tc
            mode = str(mode_raw).upper() if isinstance(mode_raw, str) else ""
            if mode in ("AUTO", "ANY", "NONE"):
                fcfg = T.FunctionCallingConfig(
                    mode=mode,
                    allowed_function_names=allowed if isinstance(allowed, list) else None,
                )
                self.cfg["tool_config"] = T.ToolConfig(function_calling_config=fcfg)
        except Exception:
            return


class GeminiBackend(ModelBackend):
    """Google Gemini backend (minimal implementation)."""

    def __init__(self) -> None:
        self._GenAIClient: Any | None = None
        self._Types: Any | None = None
        self._client_sync: Any | None = None
        self._client_async: Any | None = None
        try:
            from google import genai as _genai
            from google.genai import types as _types

            self._GenAIClient = getattr(_genai, "Client", None)
            self._Types = _types
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
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg = _prepare_config(config, output_schema)
        T = self._Types
        if T is None:
            raise ConfigurationError("Google GenAI SDK types not available")
        cfg_state = dict(cfg)
        tools_present = bool(tools)
        if tools_present:
            cfg_state.pop("response_mime_type", None)
            cfg_state.pop("response_json_schema", None)
        state = GeminiLoopState(
            types_mod=T,
            config=config,
            tools=tools or [],
            cfg=cfg_state,
            prompt=prompt,
        )
        out = self.run_tool_loop(client, state)
        if (
            isinstance(output_schema, dict)
            and bool(config.auto_finalize_missing_output)
            and should_finalize_structured_output(out, output_schema)
        ):
            text2 = _finalize_json_output(self._Types, client, model_name, state.messages, cfg)
            return text2
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
        if tools or output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        client: Any = self._client_sync
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg = _prepare_config(config, None)

        try:
            stream = client.models.generate_content_stream(
                model=model_name, contents=prompt, config=cfg or None
            )
        except Exception as e:
            raise ConfigurationError(str(e)) from e

        def gen():
            for chunk in stream:
                txt = getattr(chunk, "text", "") or ""
                if txt:
                    yield txt

        return gen()

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        client: Any = self._get_sync_client()
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg = _prepare_config(config, output_schema)
        T = self._Types
        if T is None:
            raise ConfigurationError("Google GenAI SDK types not available")
        cfg_state = dict(cfg)
        tools_present = bool(tools)
        if tools_present:
            cfg_state.pop("response_mime_type", None)
            cfg_state.pop("response_json_schema", None)
        state = GeminiLoopState(
            types_mod=T,
            config=config,
            tools=tools or [],
            cfg=cfg_state,
            prompt=prompt,
        )
        out = await self.arun_tool_loop(client, state)
        if (
            isinstance(output_schema, dict)
            and bool(config.auto_finalize_missing_output)
            and should_finalize_structured_output(out, output_schema)
        ):
            text2 = await _afinalize_json_output(
                self._Types, client, model_name, state.messages, cfg
            )
            return text2
        return out

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        _ = self._get_sync_client()
        if tools or output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        client: Any = self._client_sync
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg = _prepare_config(config, None)

        stream_ctx = await client.aio.models.generate_content_stream(
            model=model_name, contents=prompt, config=cfg or None
        )

        async def agen():
            async for chunk in stream_ctx:
                txt = getattr(chunk, "text", "") or ""
                if txt:
                    yield txt

        return agen()

    def _get_sync_client(self) -> Any:
        if self._GenAIClient is None:
            raise ConfigurationError("Google GenAI SDK not installed. Install `alloy[gemini]`.")
        if self._client_sync is None:
            self._client_sync = self._GenAIClient()
        return self._client_sync

    def _get_async_client(self) -> Any:
        return self._get_sync_client()


def _response_text(res: Any) -> str:
    txt = getattr(res, "text", None)
    if isinstance(txt, str) and txt:
        return txt
    candidates = getattr(res, "candidates", None)
    if isinstance(candidates, list) and candidates:
        cand0 = candidates[0]
        content = getattr(cand0, "content", None)
        parts = getattr(content, "parts", None)
        if isinstance(parts, list):
            out: list[str] = []
            for p in parts:
                t = getattr(p, "text", None)
                if isinstance(t, str) and t:
                    out.append(t)
            return "".join(out)
    return ""


def _extract_text_from_response(res: Any) -> str:
    parsed = getattr(res, "parsed", None)
    if parsed is not None:
        try:
            return json.dumps(parsed)
        except Exception:
            return str(parsed)
    return _response_text(res)


def _build_tools(tools: list | None, T: Any) -> tuple[list[Any] | None, dict[str, Any]]:
    def _fmt(name: str, description: str, params: dict[str, Any]) -> Any:
        return T.FunctionDeclaration(
            name=name, description=description, parameters=_schema_to_gemini(T, params)
        )

    return build_tools_common(tools, _fmt)
