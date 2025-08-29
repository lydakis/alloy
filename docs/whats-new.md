# What's New

Release notes and highlights. See full changelog for details.

- [Changelog](https://github.com/lydakis/alloy/blob/main/CHANGELOG.md)
- [Releases](https://github.com/lydakis/alloy/releases)

## 0.2.0 (2025-08-26)

- Cross‑provider streaming policy
  - Unified on text‑only streaming. Commands with tools or non‑string outputs do not stream (guarded in code and docs).
  - Examples and Getting Started updated to call this out explicitly.

- OpenAI
  - Responses API migration with shared request builder and centralized function‑calling loop via `_LoopState`.
  - Safer output assembly; always threads `previous_response_id`.
  - One follow‑up finalize (no tools) when a structured result is missing; raises `ToolLoopLimitExceeded` when the turn cap is exceeded.
  - Async parallel tool execution using `asyncio.to_thread`.

- Gemini
  - Backend refactor for non‑streaming flows: capped tool loop and strict finalize pass with the provided schema.
  - Text‑only streaming preserved; tools/structured outputs not supported in stream.

- Anthropic
  - Parity with OpenAI/Gemini for tools: robust loop with parallel tool results aggregated into a single user message.
  - Respects configured `tool_choice` (defaults to `{type:"auto"}`); supports `anthropic_disable_parallel_tool_use`.
  - Structured outputs: prefill only for non‑string primitives and object schemas; no prefill for strings; one JSON‑only finalization step after tools when needed.
  - Text‑only streaming supported; tools/structured outputs not supported in stream.

- Commands & typing
  - Enforce command prompt functions are annotated `-> str`; the decorator controls the output type.
  - Clearer parse errors and refined type stubs for default returns and async variants.

- Safety & configuration
  - Default `max_tool_turns=10` (override via `configure` or `ALLOY_MAX_TOOL_TURNS`).

- Tests & docs
  - New Anthropic integration tests: structured float/object, text‑only streaming, and parallel tool calls.
  - Docs improvements: stability page, streaming policy, configuration defaults; theme & brand refinements.

## 0.1.4 (2025-08-14)

- Typing defaults: omit `output` → `str` (async → `Awaitable[str]`); refined stubs and preserved ParamSpec; `ask.stream_async` typed.
- DBC: `ToolError` messages surface back to the model (OpenAI/Anthropic) for early corrective feedback; unit + integration tests; docs + examples.
- Docs: Typing page, Equivalence Guide, Tool Recipes, patterns examples; standardized imports and decorator style.
- Tooling: pre-commit enforcement for imports and decorator style in code + docs.

## Unreleased

- OpenAI: migrate to Responses API; shared request builder; centralized tool-call processing; safer output assembly.
- Structured Outputs (strict mode):
  - Only provider-enforced JSON Schema; no prompt shaping.
  - Fail fast for open-ended objects (`dict`, `dict[...]`, `list[dict]`) with a clear `ConfigurationError` directing users to a concrete schema (dataclass/TypedDict).
  - Dataclasses: all fields required; `additionalProperties: false`.
- Types: forward-ref dataclass coercion; unified parse path; cached type-hints; native typing.
- Commands: helper mixin for parse/retry; consistent error chaining; retry docs clarified (total attempts).
- Docs: updated “Enforcing Outputs” to describe strict-mode behavior and limitations.
  - Tool schemas are now non-strict and respect Python defaults: parameters with defaults are optional; nested dataclasses propagate optionality.
- Streaming: simplified policy — text-only across providers; commands with tools or non-string outputs do not stream; use provider SDKs for complex streaming.
- Gemini: backend refactor with non-streaming tool loop and strict finalize; streaming remains text-only.
