# What's New

Release notes and highlights. See full changelog for details.

- [Changelog](https://github.com/lydakis/alloy/blob/main/CHANGELOG.md)
- [Releases](https://github.com/lydakis/alloy/releases)

## 0.3.0 (2025-09-02)

- Finalize centralization
  - One canonical rule in `should_finalize_structured_output` handles strings (including wrapped primitives) vs. non-strings.
  - Providers defer to it; string outputs finalize only when empty.

- Shared helpers
  - `build_tools_common` for uniform tool-schema building across providers.
  - `ensure_object_schema` wraps primitives into `{ "value": ... }` consistently.

- Config extras (generic-first)
  - Use `tool_choice`, `allowed_tools`, `disable_parallel_tool_use`, `ollama_api`; provider-prefixed fallbacks supported.

- Provider parity & cleanup
  - Client getters standardized (`_get_sync_client` / `_get_async_client`).
  - Streaming: robust close/aclose for Gemini and Ollama streams; OpenAI/Anthropic already use context managers.
  - Anthropic: skip JSON prefill after tool errors so plain messages surface.
  - Ollama: remove broad exception wrapping in `complete()`; runtime errors propagate consistently.

- Docs & tests
  - Configuration extras presented as tables; production guide clarifies error surfaces and retries.
  - Tests updated for new getters; added unit tests for base helpers.

## 0.2.2 (2025-08-29)

- Shared loop & Gemini alignment
  - Centralized tool loop and provider state (`BaseLoopState`) migrated across OpenAI/Anthropic/Gemini.
  - Gemini now always uses the shared loop; finalize parity with Anthropic/OpenAI preserved.
- Streaming API: `ask.stream_async()` returns an `AsyncIterable[str]` directly (no await at call site).
- Structured outputs: providers finalize only when `auto_finalize_missing_output=True` (default on).
- OpenAI: reasoning models ignore temperature; Alloy drops it and logs a debug line.
- Fake backend: stricter schema fill (nested required properties) to mirror provider strict mode.

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
