from __future__ import annotations

from collections.abc import Iterable, AsyncIterable
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar
import inspect
import abc
import concurrent.futures
import asyncio

from ..config import Config, DEFAULT_PARALLEL_TOOLS_MAX
from ..errors import ConfigurationError, ToolError, create_tool_loop_exception
import os
import json


T = TypeVar("T")


@dataclass
class ToolCall:
    id: str | int | None
    name: str
    args: dict[str, Any]


@dataclass
class ToolResult:
    id: str | int | None
    ok: bool
    value: Any | None = None
    error: str | None = None


class BaseLoopState(Generic[T], abc.ABC):
    def __init__(self, config: Config, tool_map: dict[str, Callable[..., Any]]):
        self.config = config
        self.tool_map = tool_map
        self.turns = 0
        self.last_response_text: str = ""

    @abc.abstractmethod
    def make_request(self, client: Any) -> T: ...

    @abc.abstractmethod
    async def amake_request(self, client: Any) -> T: ...

    @abc.abstractmethod
    def extract_text(self, response: T) -> str: ...

    @abc.abstractmethod
    def extract_tool_calls(self, response: T) -> list[ToolCall] | None: ...

    @abc.abstractmethod
    def add_tool_results(self, calls: list[ToolCall], results: list[ToolResult]) -> None: ...


class ModelBackend:
    """Abstract provider interface.

    Concrete backends implement completion and tool-calling behavior.
    """

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        raise NotImplementedError

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        raise NotImplementedError

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        raise NotImplementedError

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        raise NotImplementedError

    def _execute_single_tool(
        self, call: ToolCall, tool_map: dict[str, Callable[..., Any]]
    ) -> ToolResult:
        fn = tool_map.get(call.name)
        if not fn:
            return ToolResult(call.id, ok=False, error=f"Tool '{call.name}' not available")
        try:
            args = call.args
            try:
                target_fn = getattr(getattr(fn, "spec", None), "func", None)
                if target_fn and isinstance(args, dict):
                    sig = inspect.signature(target_fn)
                    coerced: dict[str, Any] = {}
                    for name, value in args.items():
                        param = sig.parameters.get(name)
                        ann = param.annotation if param is not None else inspect._empty
                        coerced[name] = self._coerce_value(value, ann)
                    args = coerced
            except Exception:
                pass
            out = fn(**args) if isinstance(args, dict) else fn(args)
            return ToolResult(call.id, ok=True, value=out)
        except ToolError as e:
            return ToolResult(call.id, ok=False, error=str(e))
        except Exception as e:
            return ToolResult(call.id, ok=False, error=f"{type(e).__name__}: {e}")

    @staticmethod
    def _coerce_value(value: Any, annotation: Any) -> Any:
        try:
            if annotation is int:
                return int(value)
            if annotation is float:
                return float(value)
            if annotation is bool:
                if isinstance(value, bool):
                    return value
                s = str(value).strip().lower()
                return s in ("true", "1", "yes", "y", "t", "on")
            if annotation is str:
                return str(value)
        except Exception:
            return value
        return value

    def execute_tools(
        self,
        calls: list[ToolCall],
        *,
        parallel_tools_max: int,
        tool_map: dict[str, Callable[..., Any]],
    ) -> list[ToolResult]:
        if not calls:
            return []
        if len(calls) == 1:
            return [self._execute_single_tool(calls[0], tool_map)]
        max_workers = max(1, min(len(calls), parallel_tools_max))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = [ex.submit(self._execute_single_tool, c, tool_map) for c in calls]
            return [f.result() for f in futs]

    async def aexecute_tools(
        self,
        calls: list[ToolCall],
        *,
        parallel_tools_max: int,
        tool_map: dict[str, Callable[..., Any]],
    ) -> list[ToolResult]:
        if not calls:
            return []
        sem = asyncio.Semaphore(max(1, parallel_tools_max))

        async def run(c: ToolCall) -> ToolResult:
            async with sem:
                return await asyncio.to_thread(self._execute_single_tool, c, tool_map)

        return await asyncio.gather(*(run(c) for c in calls))

    def run_tool_loop(self, client: Any, state: BaseLoopState[T]) -> str:
        while True:
            resp = state.make_request(client)
            text = state.extract_text(resp)
            state.last_response_text = text

            calls = state.extract_tool_calls(resp) or []
            if not calls:
                return text

            state.turns += 1
            lim = state.config.max_tool_turns
            if isinstance(lim, int) and lim >= 0 and state.turns > lim:
                raise create_tool_loop_exception(
                    max_turns=lim, turns_taken=state.turns, partial_text=state.last_response_text
                )

            ptm_raw = state.config.parallel_tools_max
            ptm = (
                ptm_raw if isinstance(ptm_raw, int) and ptm_raw > 0 else DEFAULT_PARALLEL_TOOLS_MAX
            )
            results = self.execute_tools(calls, parallel_tools_max=ptm, tool_map=state.tool_map)
            state.add_tool_results(calls, results)

    async def arun_tool_loop(self, client: Any, state: BaseLoopState[T]) -> str:
        while True:
            resp = await state.amake_request(client)
            text = state.extract_text(resp)
            state.last_response_text = text

            calls = state.extract_tool_calls(resp) or []
            if not calls:
                return text

            state.turns += 1
            lim = state.config.max_tool_turns
            if isinstance(lim, int) and lim >= 0 and state.turns > lim:
                raise create_tool_loop_exception(
                    max_turns=lim, turns_taken=state.turns, partial_text=state.last_response_text
                )

            ptm_raw = state.config.parallel_tools_max
            ptm = (
                ptm_raw if isinstance(ptm_raw, int) and ptm_raw > 0 else DEFAULT_PARALLEL_TOOLS_MAX
            )
            results = await self.aexecute_tools(
                calls, parallel_tools_max=ptm, tool_map=state.tool_map
            )
            state.add_tool_results(calls, results)


def should_finalize_structured_output(text: str, schema: dict | None) -> bool:
    """Return True if a finalize turn should be attempted for typed outputs.

    Finalize when a schema is provided and the current text is empty or not
    valid JSON (after stripping optional code fences). This is a lightweight
    validity check; providers perform the strict parse.
    """
    if not isinstance(schema, dict):
        return False
    s = (text or "").strip()
    if not s:
        return True
    if s.startswith("```"):
        nl = s.find("\n")
        if nl != -1:
            s = s[nl + 1 :]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    try:
        json.loads(s)
        return False
    except Exception:
        return True


def serialize_tool_payload(payload: object) -> str:
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload)
    except Exception:
        return str(payload)


def build_tools_common(
    tools: list | None,
    formatter: Callable[[str, str, dict[str, Any]], Any],
) -> tuple[list[Any] | None, dict[str, Any]]:
    if not tools:
        return None, {}
    defs: list[Any] = []
    tool_map: dict[str, Any] = {}
    for t in tools:
        spec = t.spec.as_schema()
        params = spec.get("parameters") if isinstance(spec, dict) else None
        if not isinstance(params, dict):
            params = {"type": "object"}
        defs.append(formatter(t.spec.name, t.spec.description, params))
        tool_map[t.spec.name] = t
    return defs, tool_map


def get_backend(model: str | None) -> ModelBackend:
    if not model:
        raise ConfigurationError("No model configured. Call alloy.configure(model=...) first.")
    if os.environ.get("ALLOY_BACKEND", "").lower() == "fake":

        class _Fake(ModelBackend):
            def _fake_from_schema(self, schema: object) -> object:
                if not isinstance(schema, dict):
                    return "demo"
                t = (schema.get("type") or "").lower()
                if t == "object":
                    props = (
                        schema.get("properties", {})
                        if isinstance(schema.get("properties"), dict)
                        else {}
                    )
                    required = (
                        schema.get("required", [])
                        if isinstance(schema.get("required"), list)
                        else []
                    )
                    keys = list(required) if required else list(props.keys())
                    out: dict[str, object] = {}
                    for k in keys:
                        out[k] = self._fake_from_schema(props.get(k, {}))
                    return out
                if t == "array":
                    return []
                if t == "number":
                    return 0.0
                if t == "integer":
                    return 0
                if t == "boolean":
                    return True
                if t == "null":
                    return None
                return "demo"

            def complete(
                self, prompt: str, *, tools=None, output_schema=None, config: Config
            ) -> str:
                if isinstance(output_schema, dict) and output_schema.get("type") == "object":
                    return json.dumps(self._fake_from_schema(output_schema))
                return "42"

            def stream(self, prompt: str, *, tools=None, output_schema=None, config: Config):
                yield "demo"

            async def acomplete(
                self, prompt: str, *, tools=None, output_schema=None, config: Config
            ) -> str:
                return self.complete(
                    prompt, tools=tools, output_schema=output_schema, config=config
                )

            async def astream(self, prompt: str, *, tools=None, output_schema=None, config: Config):
                async def agen():
                    yield "demo"

                return agen()

        return _Fake()
    name = model.lower()
    if name.startswith("ollama:") or name.startswith("local:"):
        from .ollama import OllamaBackend

        return OllamaBackend()
    if name.startswith("claude") or name.startswith("anthropic"):
        from .anthropic import AnthropicBackend

        return AnthropicBackend()
    if name.startswith("gemini") or name.startswith("google"):
        from .gemini import GeminiBackend

        return GeminiBackend()
    if (
        name.startswith("gpt")
        or name.startswith("openai")
        or "gpt-" in name
        or name.startswith("o1")
        or name.startswith("o3")
        or name.startswith("o4")
    ):
        from .openai import OpenAIBackend

        return OpenAIBackend()

    raise ConfigurationError(f"No backend available for model '{model}'.")
