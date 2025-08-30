from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any, cast
import json

from ..config import Config
from ..errors import (
    ConfigurationError,
)
from .base import ModelBackend, BaseLoopState, ToolCall, ToolResult


def _prepare_config(config: Config, output_schema: dict | None) -> tuple[dict[str, object], bool]:
    cfg: dict[str, object] = {}
    if config.default_system:
        cfg["system_instruction"] = str(config.default_system)
    if config.temperature is not None:
        cfg["temperature"] = float(config.temperature)
    if config.max_tokens is not None:
        cfg["max_output_tokens"] = int(config.max_tokens)
    wrapped_primitive = False
    if output_schema and isinstance(output_schema, dict):
        schema: dict[str, object] = output_schema
        if schema.get("type") != "object":
            schema = {
                "type": "object",
                "properties": {"value": output_schema},
                "required": ["value"],
            }
            wrapped_primitive = True
        cfg["response_mime_type"] = "application/json"
        cfg["response_json_schema"] = schema
    return cfg, wrapped_primitive


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
    T: Any, client: Any, model_name: str, history: list[Any], cfg: dict[str, object]
) -> str:
    if T is None:
        raise ConfigurationError("Google GenAI SDK types not available")
    cfg2 = dict(cfg)
    cfg2.pop("tools", None)
    cfg2.pop("automatic_function_calling", None)
    finalize_msg = T.Content(
        role="user",
        parts=[
            T.Part.from_text(
                text=(
                    "Return only a JSON object that matches the required schema. "
                    "No extra text or code fences."
                )
            )
        ],
    )

    def _finalize_once(msg: Any) -> tuple[str, Any]:
        res = client.models.generate_content(
            model=model_name, contents=history + [msg], config=cfg2 or None
        )
        txt = _extract_text_from_response(res)
        parsed = getattr(res, "parsed", None)
        return txt, parsed

    txt, parsed = _finalize_once(finalize_msg)
    if parsed is not None and str(txt).strip():
        return txt

    strict_msg = T.Content(
        role="user",
        parts=[
            T.Part.from_text(
                text=(
                    "Respond ONLY with the JSON object matching the required schema. No extra text, no backticks."
                )
            )
        ],
    )
    txt2, _parsed2 = _finalize_once(strict_msg)
    return txt2


async def _afinalize_json_output(
    T: Any, client: Any, model_name: str, history: list[Any], cfg: dict[str, object]
) -> str:
    if T is None:
        raise ConfigurationError("Google GenAI SDK types not available")
    cfg2 = dict(cfg)
    cfg2.pop("tools", None)
    cfg2.pop("automatic_function_calling", None)
    finalize_msg = T.Content(
        role="user",
        parts=[
            T.Part.from_text(
                text=(
                    "Return only a JSON object that matches the required schema. "
                    "No extra text or code fences."
                )
            )
        ],
    )

    async def _finalize_once(msg: Any) -> tuple[str, Any]:
        res = await client.aio.models.generate_content(
            model=model_name, contents=history + [msg], config=cfg2 or None
        )
        txt = _extract_text_from_response(res)
        parsed = getattr(res, "parsed", None)
        return txt, parsed

    txt, parsed = await _finalize_once(finalize_msg)
    if parsed is not None and str(txt).strip():
        return txt
    strict_msg = T.Content(
        role="user",
        parts=[
            T.Part.from_text(
                text=(
                    "Respond ONLY with the JSON object matching the required schema. No extra text, no backticks."
                )
            )
        ],
    )
    txt2, _parsed2 = await _finalize_once(strict_msg)
    return txt2


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
        decls = []
        self.tool_map: dict[str, Any] = {}
        for tl in tools:
            spec = tl.spec.as_schema()
            params = spec.get("parameters") if isinstance(spec, dict) else None
            if not isinstance(params, dict):
                params = {"type": "object"}
            decls.append(
                self.T.FunctionDeclaration(
                    name=tl.spec.name,
                    description=tl.spec.description,
                    parameters=_schema_to_gemini(self.T, params),
                )
            )
            self.tool_map[tl.spec.name] = tl
        self.cfg["tools"] = [self.T.Tool(function_declarations=decls)]
        self.cfg["automatic_function_calling"] = self.T.AutomaticFunctionCallingConfig(disable=True)
        self.history: list[Any] = [
            self.T.Content(role="user", parts=[self.T.Part.from_text(text=prompt)])
        ]
        self._last_assistant_content: Any | None = None

    def _apply_tool_choice(self) -> None:
        T = self.T
        if T is None:
            return
        extra = getattr(self.config, "extra", {}) or {}
        try:
            mode_raw = extra.get("gemini_tool_mode") if isinstance(extra, dict) else None
            mode = str(mode_raw).upper() if isinstance(mode_raw, str) else ""
            allowed = (
                extra.get("gemini_allowed_function_names") if isinstance(extra, dict) else None
            )
            if mode in ("AUTO", "ANY", "NONE"):
                fcfg = T.FunctionCallingConfig(
                    mode=mode,
                    allowed_function_names=allowed if isinstance(allowed, list) else None,
                )
                self.cfg["tool_config"] = T.ToolConfig(function_calling_config=fcfg)
        except Exception:
            return

    def make_request(self, client: Any) -> Any:
        self._apply_tool_choice()
        return client.models.generate_content(
            model=self.config.model, contents=self.history, config=self.cfg or None
        )

    async def amake_request(self, client: Any) -> Any:
        self._apply_tool_choice()
        return await client.aio.models.generate_content(
            model=self.config.model, contents=self.history, config=self.cfg or None
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
            self.history.append(self._last_assistant_content)
        for call, res in zip(calls, results):
            payload = res.value if res.ok else res.error
            response_obj = payload if isinstance(payload, (dict, list)) else {"result": payload}
            resp_part = self.T.Part.from_function_response(
                name=(call.name or "unknown"), response=response_obj
            )
            self.history.append(self.T.Content(role="tool", parts=[resp_part]))


class GeminiBackend(ModelBackend):
    """Google Gemini backend (minimal implementation)."""

    def __init__(self) -> None:
        self._GenAIClient: Any | None = None
        self._Types: Any | None = None
        self._client: Any | None = None
        try:
            from google import genai as _genai
            from google.genai import types as _types

            self._GenAIClient = getattr(_genai, "Client", None)
            self._Types = _types
        except Exception:
            pass

    def _get_client(self) -> Any:
        if self._GenAIClient is None:
            raise ConfigurationError("Google GenAI SDK not installed. Install `alloy[gemini]`.")
        if self._client is None:
            self._client = self._GenAIClient()
        return self._client

    @staticmethod
    def _prepare_tool_config(T: Any, config: Config) -> Any | None:
        try:
            extra = getattr(config, "extra", {}) or {}
            mode_raw = extra.get("gemini_tool_mode", "")
            mode = str(mode_raw).upper() if isinstance(mode_raw, str) else ""
            allowed = extra.get("gemini_allowed_function_names")
            if mode in ("AUTO", "ANY", "NONE"):
                fcfg = T.FunctionCallingConfig(
                    mode=mode,
                    allowed_function_names=allowed if isinstance(allowed, list) else None,
                )
                return T.ToolConfig(function_calling_config=fcfg)
        except Exception:
            return None
        return None

    def _apply_tool_choice(
        self, cfg: dict[str, object], tools_present: bool, extra: Any, tool_turns: int
    ) -> None:
        if not tools_present:
            cfg.pop("tool_config", None)
            return
        T = self._Types
        if T is None:
            return
        try:
            mode_raw = extra.get("gemini_tool_mode") if isinstance(extra, dict) else None
            mode = str(mode_raw).upper() if isinstance(mode_raw, str) else ""
            allowed = (
                extra.get("gemini_allowed_function_names") if isinstance(extra, dict) else None
            )
            if mode in ("AUTO", "ANY", "NONE"):
                fcfg = T.FunctionCallingConfig(
                    mode=mode,
                    allowed_function_names=allowed if isinstance(allowed, list) else None,
                )
                cfg["tool_config"] = T.ToolConfig(function_calling_config=fcfg)
        except Exception:
            return

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        client: Any = self._get_client()
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg, wrapped_primitive = _prepare_config(config, output_schema)
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
        if (output_schema is not None) and bool(config.auto_finalize_missing_output):
            if tools_present or not out.strip():
                text2 = _finalize_json_output(self._Types, client, model_name, state.history, cfg)
                return _unwrap_value_if_needed(text2, wrapped_primitive)
        return _unwrap_value_if_needed(out, wrapped_primitive)

        try:
            res_new = client.models.generate_content(
                model=model_name, contents=prompt, config=cfg or None
            )
            text = _extract_text_from_response(res_new)
            should_finalize = (
                output_schema is not None
                and (config.auto_finalize_missing_output is not False)
                and not text.strip()
            )
            if should_finalize:
                T = self._Types
                if T is None:
                    raise ConfigurationError("Google GenAI SDK types not available")
                user_content = T.Content(role="user", parts=[T.Part.from_text(text=prompt)])
                candidates = getattr(res_new, "candidates", None)
                assistant_content = (
                    getattr(candidates[0], "content", None)
                    if isinstance(candidates, list) and candidates
                    else None
                )
                history = [c for c in [user_content, assistant_content] if c is not None]
                text2 = _finalize_json_output(self._Types, client, model_name, history, cfg)
                return _unwrap_value_if_needed(text2, wrapped_primitive)
            return _unwrap_value_if_needed(text, wrapped_primitive)
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
        _ = self._get_client()
        if tools or output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        client: Any = self._client
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg, _wrapped = _prepare_config(config, None)

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
        client: Any = self._get_client()
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg, wrapped_primitive = _prepare_config(config, output_schema)
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
        if (output_schema is not None) and bool(config.auto_finalize_missing_output):
            if tools_present or not out.strip():
                text2 = await _afinalize_json_output(
                    self._Types, client, model_name, state.history, cfg
                )
                return _unwrap_value_if_needed(text2, wrapped_primitive)
        return _unwrap_value_if_needed(out, wrapped_primitive)

        try:
            res = await client.aio.models.generate_content(
                model=model_name, contents=prompt, config=cfg or None
            )
            text = _extract_text_from_response(res)
            should_finalize = (
                output_schema is not None
                and (config.auto_finalize_missing_output is not False)
                and not text.strip()
            )
            if should_finalize:
                T = self._Types
                if T is None:
                    raise ConfigurationError("Google GenAI SDK types not available")
                user_content = T.Content(role="user", parts=[T.Part.from_text(text=prompt)])
                candidates = getattr(res, "candidates", None)
                assistant_content = (
                    getattr(candidates[0], "content", None)
                    if isinstance(candidates, list) and candidates
                    else None
                )
                history = [c for c in [user_content, assistant_content] if c is not None]
                text2 = await _afinalize_json_output(self._Types, client, model_name, history, cfg)
                return _unwrap_value_if_needed(text2, wrapped_primitive)
            return _unwrap_value_if_needed(text, wrapped_primitive)
        except Exception as e:
            raise ConfigurationError(str(e)) from e

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        _ = self._get_client()
        if tools or output_schema is not None:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        client: Any = self._client
        model_name = config.model
        if not model_name:
            raise ConfigurationError(
                "A model name must be specified in the configuration for the Gemini backend."
            )
        cfg, _wrapped = _prepare_config(config, None)

        stream_ctx = await client.aio.models.generate_content_stream(
            model=model_name, contents=prompt, config=cfg or None
        )

        async def agen():
            async for chunk in stream_ctx:
                txt = getattr(chunk, "text", "") or ""
                if txt:
                    yield txt

        return agen()


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


def _unwrap_value_if_needed(text: str, wrapped_primitive: bool) -> str:
    if not wrapped_primitive or not text:
        return text
    try:
        data = json.loads(text)
    except Exception:
        return text
    if isinstance(data, dict) and "value" in data:
        try:
            return str(data["value"])
        except Exception:
            return text
    return text
