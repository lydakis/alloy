from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from typing import Any
import json

from ..config import Config
from ..errors import ConfigurationError
from .base import (
    ModelBackend,
    BaseLoopState,
    ToolCall,
    ToolResult,
    should_finalize_structured_output,
    serialize_tool_payload,
)


def _extract_model_name(model: str | None) -> str:
    if not model:
        return ""
    if model.startswith("ollama:"):
        return model.split(":", 1)[1]
    if model.startswith("local:"):
        return model.split(":", 1)[1]
    return model


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
                "function": {
                    "name": t.spec.name,
                    "description": t.spec.description,
                    "parameters": params,
                },
            }
        )
        tool_map[t.spec.name] = t
    return tool_defs, tool_map


def _wrap_schema_for_primitives(schema: dict | None) -> dict | None:
    if not isinstance(schema, dict):
        return None
    if (schema.get("type") or "").lower() != "object":
        return {
            "type": "object",
            "properties": {"value": schema},
            "required": ["value"],
        }
    return schema


def _strip_code_fences(text: str) -> str:
    if not isinstance(text, str):
        return text
    s = text.strip()
    if s.startswith("```"):
        nl = s.find("\n")
        if nl != -1:
            s = s[nl + 1 :]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


class OllamaLoopState(BaseLoopState[Any]):
    def __init__(
        self,
        *,
        prompt: str,
        config: Config,
        model_name: str,
        tool_defs: list[dict] | None,
        tool_map: dict[str, Any],
        output_schema: dict | None,
    ) -> None:
        super().__init__(config, tool_map=tool_map)
        self.model_name = model_name
        self.tool_defs = tool_defs
        self.output_schema = output_schema
        self.messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        self._last_assistant_content: dict[str, Any] | None = None

    def make_request(self, client: Any) -> Any:
        use_format = bool(self.output_schema) and self.tool_defs is None and len(self.messages) == 1
        kwargs = self._build_chat_kwargs(use_format)
        return client.chat(**kwargs)

    async def amake_request(self, client: Any) -> Any:
        use_format = bool(self.output_schema) and self.tool_defs is None and len(self.messages) == 1
        kwargs = self._build_chat_kwargs(use_format)
        return await client.chat(**kwargs)

    def extract_text(self, response: Any) -> str:
        raw_msg = (
            response.get("message", {})
            if isinstance(response, dict)
            else getattr(response, "message", {})
        )
        if isinstance(raw_msg, dict):
            msg_dict = raw_msg
        else:
            try:
                msg_dict = raw_msg.model_dump()
            except Exception:
                msg_dict = {
                    "role": getattr(raw_msg, "role", None),
                    "content": getattr(raw_msg, "content", ""),
                }
        self._last_assistant_content = msg_dict
        content = msg_dict.get("content", "")
        return content or ""

    def extract_tool_calls(self, response: Any) -> list[ToolCall] | None:
        msg = self._last_assistant_content or {}
        tc = msg.get("tool_calls") if isinstance(msg, dict) else None
        calls: list[ToolCall] = []
        if isinstance(tc, list):
            for entry in tc:
                fn = entry.get("function") if isinstance(entry, dict) else None
                if isinstance(fn, dict):
                    name = str(fn.get("name") or "")
                    raw_args = fn.get("arguments")
                    if isinstance(raw_args, dict):
                        args = raw_args
                    elif isinstance(raw_args, str):
                        try:
                            parsed = json.loads(raw_args)
                            args = parsed if isinstance(parsed, dict) else {}
                        except Exception:
                            args = {}
                    else:
                        args = {}
                    calls.append(ToolCall(id=None, name=name, args=args))
        return calls

    def add_tool_results(self, calls: list[ToolCall], results: list[ToolResult]) -> None:
        if isinstance(self._last_assistant_content, dict):
            self.messages.append(self._last_assistant_content)
        for call, res in zip(calls, results):
            payload = res.value if res.ok else (res.error or "")
            content = serialize_tool_payload(payload)
            self.messages.append({"role": "tool", "content": content, "tool_name": call.name or ""})

    def _build_chat_kwargs(self, use_format: bool, stream: bool = False) -> dict[str, Any]:
        msgs = list(self.messages)
        if use_format and isinstance(self.output_schema, dict):
            msgs = msgs + [
                {
                    "role": "user",
                    "content": (
                        "Respond ONLY with the JSON object matching the required schema. "
                        "No extra text or code fences."
                    ),
                }
            ]
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": msgs,
            "stream": bool(stream),
        }
        system_text = self.config.default_system or ""
        if system_text:
            kwargs["messages"] = [{"role": "system", "content": system_text}] + kwargs["messages"]
        opts: dict[str, Any] = {}
        if self.config.temperature is not None:
            opts["temperature"] = float(self.config.temperature)
        if self.config.max_tokens is not None:
            opts["num_predict"] = int(self.config.max_tokens)
        if opts:
            kwargs["options"] = opts
        if self.tool_defs is not None:
            kwargs["tools"] = self.tool_defs
        if use_format and isinstance(self.output_schema, dict):
            kwargs["format"] = _wrap_schema_for_primitives(self.output_schema)
        return kwargs


class OllamaOpenAIChatLoopState(BaseLoopState[Any]):
    def __init__(
        self,
        *,
        prompt: str,
        config: Config,
        model_name: str,
        tool_defs: list[dict] | None,
        tool_map: dict[str, Any],
        output_schema: dict | None,
    ) -> None:
        super().__init__(config, tool_map=tool_map)
        self.model_name = model_name
        self.tool_defs = tool_defs
        self.output_schema = output_schema
        self.messages: list[dict[str, Any]] = []
        if config.default_system:
            self.messages.append({"role": "system", "content": str(config.default_system)})
        self.messages.append({"role": "user", "content": prompt})
        self._last_assistant_content: dict[str, Any] | None = None

    def make_request(self, client: Any) -> Any:
        cli = client if client is not None else self._client()
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": self.messages,
        }
        if self.tool_defs is not None:
            kwargs["tools"] = self.tool_defs
        extra = getattr(self.config, "extra", {}) or {}
        choice = None
        if isinstance(extra, dict):
            choice = extra.get("tool_choice") or extra.get("ollama_tool_choice")
        if isinstance(choice, (str, dict)):
            kwargs["tool_choice"] = choice
        res = cli.chat.completions.create(**kwargs)
        return res

    async def amake_request(self, client: Any) -> Any:
        try:
            from openai import AsyncOpenAI
        except Exception as e:
            raise ConfigurationError(
                "OpenAI SDK not available for Ollama Chat Completions path"
            ) from e
        cli = (
            client
            if client is not None
            else AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        )
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": self.messages,
        }
        if self.tool_defs is not None:
            kwargs["tools"] = self.tool_defs
        extra = getattr(self.config, "extra", {}) or {}
        choice = None
        if isinstance(extra, dict):
            choice = extra.get("tool_choice") or extra.get("ollama_tool_choice")
        if isinstance(choice, (str, dict)):
            kwargs["tool_choice"] = choice
        res = await cli.chat.completions.create(**kwargs)
        return res

    def extract_text(self, response: Any) -> str:
        try:
            choice = response.choices[0]
            msg = choice.message
            self._last_assistant_content = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in (msg.tool_calls or [])
                ],
            }
            content = _strip_code_fences(msg.content or "")
            return content
        except Exception:
            return ""

    def extract_tool_calls(self, response: Any) -> list[ToolCall] | None:
        msg = self._last_assistant_content or {}
        tcs = msg.get("tool_calls") or []
        calls: list[ToolCall] = []
        for entry in tcs:
            fn = entry.get("function") if isinstance(entry, dict) else None
            if isinstance(fn, dict):
                name = str(fn.get("name") or "")
                raw = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw)
                    if not isinstance(args, dict):
                        args = {}
                except Exception:
                    args = {}
                calls.append(ToolCall(id=entry.get("id"), name=name, args=args))
        return calls

    def add_tool_results(self, calls: list[ToolCall], results: list[ToolResult]) -> None:
        if self._last_assistant_content:
            self.messages.append(self._last_assistant_content)
        for call, res in zip(calls, results):
            payload = res.value if res.ok else (res.error or "")
            content = payload if isinstance(payload, str) else json.dumps(payload)
            self.messages.append(
                {"role": "tool", "tool_call_id": call.id or "", "content": content}
            )

    def _client(self):
        try:
            from openai import OpenAI

            return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        except Exception as e:
            raise ConfigurationError(
                "OpenAI SDK not available for Ollama Chat Completions path"
            ) from e


class OllamaBackend(ModelBackend):
    """Ollama backend using the `ollama` Python SDK (chat endpoint).

    Supports native tool-calling and strict structured outputs via the `format`
    parameter on /api/chat, aligned with the shared tool loop semantics.
    """

    def __init__(self) -> None:
        self._ollama_module: Any | None = None
        self._async_client: Any | None = None
        self._OpenAI: Any | None = None
        self._AsyncOpenAI: Any | None = None
        self._openai_client: Any | None = None
        self._openai_client_async: Any | None = None

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        model_name = _extract_model_name(config.model)
        if not model_name:
            raise ConfigurationError("Ollama model not specified (use model='ollama:<name>')")
        extra = getattr(config, "extra", {}) or {}
        api_pref = (extra.get("ollama_api") or "").lower() if isinstance(extra, dict) else ""
        use_openai_chat = api_pref == "openai_chat"

        tool_defs, tool_map = _build_tools(tools)
        if use_openai_chat:
            state_oai = OllamaOpenAIChatLoopState(
                prompt=prompt,
                config=config,
                model_name=model_name,
                tool_defs=tool_defs,
                tool_map=tool_map,
                output_schema=output_schema if isinstance(output_schema, dict) else None,
            )
            try:
                oai_client = self._get_openai_client()
                out = self.run_tool_loop(oai_client, state_oai)
                if isinstance(output_schema, dict):
                    out = _strip_code_fences(out)
                if (
                    isinstance(output_schema, dict)
                    and bool(config.auto_finalize_missing_output)
                    and should_finalize_structured_output(out, output_schema)
                ):
                    state_oai.messages.append(
                        {
                            "role": "user",
                            "content": "Respond ONLY with the JSON object matching the required schema.",
                        }
                    )
                    out2 = self.run_tool_loop(oai_client, state_oai)
                    out2 = _strip_code_fences(out2)
                    return out2 if out2.strip() else out
                return out
            except Exception as e:
                from ..errors import ToolLoopLimitExceeded

                if isinstance(e, ToolLoopLimitExceeded):
                    raise
                raise ConfigurationError(str(e)) from e
        else:
            client = self._get_sync_client()
            state_native = OllamaLoopState(
                prompt=prompt,
                config=config,
                model_name=model_name,
                tool_defs=tool_defs,
                tool_map=tool_map,
                output_schema=output_schema if isinstance(output_schema, dict) else None,
            )
            try:
                out = self.run_tool_loop(client, state_native)
                if isinstance(output_schema, dict) and bool(config.auto_finalize_missing_output):
                    if should_finalize_structured_output(out, output_schema):
                        return self._finalize_json_output(client, state_native)
                return out
            except Exception as e:
                from ..errors import ToolLoopLimitExceeded

                if isinstance(e, ToolLoopLimitExceeded):
                    raise
                raise ConfigurationError(str(e)) from e

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        if tools or output_schema:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        model_name = _extract_model_name(config.model)
        if not model_name:
            raise ConfigurationError("Ollama model not specified (use model='ollama:<name>')")
        extra = getattr(config, "extra", {}) or {}
        api_pref = (extra.get("ollama_api") or "").lower() if isinstance(extra, dict) else ""
        use_openai_chat = api_pref == "openai_chat"

        messages: list[dict[str, Any]] = []
        if config.default_system:
            messages.append({"role": "system", "content": str(config.default_system)})
        messages.append({"role": "user", "content": prompt})

        if use_openai_chat:
            cli = self._get_openai_client()
            stream = cli.chat.completions.create(model=model_name, messages=messages, stream=True)

            def gen() -> Iterable[str]:
                try:
                    for event in stream:
                        try:
                            delta = event.choices[0].delta
                            piece = getattr(delta, "content", None)
                        except Exception:
                            piece = None
                        if isinstance(piece, str) and piece:
                            yield piece
                finally:
                    try:
                        stream.close()
                    except Exception:
                        pass

            return gen()
        else:
            client = self._get_sync_client()
            kwargs: dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "stream": True,
            }
            opts: dict[str, Any] = {}
            if config.temperature is not None:
                opts["temperature"] = float(config.temperature)
            if config.max_tokens is not None:
                opts["num_predict"] = int(config.max_tokens)
            if opts:
                kwargs["options"] = opts
            it = client.chat(**kwargs)

            def gen() -> Iterable[str]:
                for chunk in it:
                    try:
                        msg = getattr(chunk, "message", None)
                        piece = getattr(msg, "content", None)
                        if isinstance(piece, str) and piece:
                            yield piece
                    except Exception:
                        continue

            return gen()

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        model_name = _extract_model_name(config.model)
        if not model_name:
            raise ConfigurationError("Ollama model not specified (use model='ollama:<name>')")
        extra = getattr(config, "extra", {}) or {}
        api_pref = (extra.get("ollama_api") or "").lower() if isinstance(extra, dict) else ""
        use_openai_chat = api_pref == "openai_chat"

        tool_defs, tool_map = _build_tools(tools)
        if use_openai_chat:
            state_oai = OllamaOpenAIChatLoopState(
                prompt=prompt,
                config=config,
                model_name=model_name,
                tool_defs=tool_defs,
                tool_map=tool_map,
                output_schema=output_schema if isinstance(output_schema, dict) else None,
            )
            oai_client = self._get_async_openai_client()
            out = await self.arun_tool_loop(oai_client, state_oai)
            if isinstance(output_schema, dict):
                out = _strip_code_fences(out)
            if (
                isinstance(output_schema, dict)
                and bool(config.auto_finalize_missing_output)
                and should_finalize_structured_output(out, output_schema)
            ):
                state_oai.messages.append(
                    {
                        "role": "user",
                        "content": "Respond ONLY with the JSON object matching the required schema.",
                    }
                )
                out2 = await self.arun_tool_loop(oai_client, state_oai)
                out2 = _strip_code_fences(out2)
                return out2 if (out2 or "").strip() else out
            return out
        else:
            client = await self._get_async_client()
            state_native = OllamaLoopState(
                prompt=prompt,
                config=config,
                model_name=model_name,
                tool_defs=tool_defs,
                tool_map=tool_map,
                output_schema=output_schema if isinstance(output_schema, dict) else None,
            )
            out = await self.arun_tool_loop(client, state_native)
            if (
                isinstance(output_schema, dict)
                and bool(config.auto_finalize_missing_output)
                and should_finalize_structured_output(out, output_schema)
            ):
                return await self._afinalize_json_output(client, state_native)
            return out

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        if tools or output_schema:
            raise ConfigurationError(
                "Streaming supports text only; tools and structured outputs are not supported"
            )
        model_name = _extract_model_name(config.model)
        if not model_name:
            raise ConfigurationError("Ollama model not specified (use model='ollama:<name>')")
        extra = getattr(config, "extra", {}) or {}
        api_pref = (extra.get("ollama_api") or "").lower() if isinstance(extra, dict) else ""
        use_openai_chat = api_pref == "openai_chat"

        messages: list[dict[str, Any]] = []
        if config.default_system:
            messages.append({"role": "system", "content": str(config.default_system)})
        messages.append({"role": "user", "content": prompt})

        if use_openai_chat:
            cli = self._get_async_openai_client()
            stream = await cli.chat.completions.create(
                model=model_name, messages=messages, stream=True
            )

            async def agen() -> AsyncIterable[str]:
                async for event in stream:
                    try:
                        delta = event.choices[0].delta
                        piece = getattr(delta, "content", None)
                    except Exception:
                        piece = None
                    if isinstance(piece, str) and piece:
                        yield piece

            return agen()
        else:
            client = await self._get_async_client()
            kwargs: dict[str, Any] = {"model": model_name, "messages": messages, "stream": True}
            opts: dict[str, Any] = {}
            if config.temperature is not None:
                opts["temperature"] = float(config.temperature)
            if config.max_tokens is not None:
                opts["num_predict"] = int(config.max_tokens)
            if opts:
                kwargs["options"] = opts
            stream = await client.chat(**kwargs)

            async def agen() -> AsyncIterable[str]:
                async for chunk in stream:
                    try:
                        msg = getattr(chunk, "message", None)
                        piece = getattr(msg, "content", None)
                        if isinstance(piece, str) and piece:
                            yield piece
                    except Exception:
                        continue

            return agen()

    def _get_sync_client(self) -> Any:
        if self._ollama_module is None:
            try:
                import ollama

                self._ollama_module = ollama
            except Exception as e:
                raise ConfigurationError(
                    "Ollama SDK not installed. Run `pip install alloy[ollama]`."
                ) from e
        return self._ollama_module

    async def _get_async_client(self) -> Any:
        if self._async_client is None:
            try:
                from ollama import AsyncClient

                self._async_client = AsyncClient()
            except Exception as e:
                raise ConfigurationError(
                    "Ollama SDK not installed. Run `pip install alloy[ollama]`."
                ) from e
        return self._async_client

    def _get_openai_client(self) -> Any:
        if self._OpenAI is None:
            try:
                from openai import OpenAI

                self._OpenAI = OpenAI
            except Exception as e:
                raise ConfigurationError(
                    "OpenAI SDK not available for Ollama Chat Completions path"
                ) from e
        if self._openai_client is None:
            self._openai_client = self._OpenAI(
                base_url="http://localhost:11434/v1", api_key="ollama"
            )
        return self._openai_client

    def _get_async_openai_client(self) -> Any:
        if self._AsyncOpenAI is None:
            try:
                from openai import AsyncOpenAI

                self._AsyncOpenAI = AsyncOpenAI
            except Exception as e:
                raise ConfigurationError(
                    "OpenAI SDK not available for Ollama Chat Completions path"
                ) from e
        if self._openai_client_async is None:
            self._openai_client_async = self._AsyncOpenAI(
                base_url="http://localhost:11434/v1", api_key="ollama"
            )
        return self._openai_client_async

    def _finalize_json_output(self, client: Any, state: "OllamaLoopState") -> str:
        kwargs = state._build_chat_kwargs(use_format=True, stream=False)
        kwargs.pop("tools", None)
        res = client.chat(**kwargs)
        msg = res.get("message", {}) if isinstance(res, dict) else getattr(res, "message", {})
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        return content or ""

    async def _afinalize_json_output(self, aclient: Any, state: "OllamaLoopState") -> str:
        kwargs = state._build_chat_kwargs(use_format=True, stream=False)
        kwargs.pop("tools", None)
        res = await aclient.chat(**kwargs)
        msg = res.get("message", {}) if isinstance(res, dict) else getattr(res, "message", {})
        content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
        return content or ""
