# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to
Semantic Versioning.

## [Unreleased]

## [0.3.1] - 2025-09-06
### Fixes and Improvements
- Tool payload normalization: central helper converts dataclasses and containers to JSON‑safe structures; all providers use consistent serialization.
- Anthropic structured outputs: provider‑native guidance with precise nested key hints; minimal object prefill ("{") only; remove unsupported response_format usage. Single strict finalize turn when needed.
- Gemini tools: suppress SDK non‑text warnings by reading `candidates.content.parts`; ensure `FunctionResponse.response` is a dict (wrap scalars as `{ "result": ... }`).
- Ollama:
  - Native path unchanged (strict schema via `format`).
  - OpenAI‑chat path adds strict nested‑keys finalize hints where schema cannot be enforced.
  - Split dataclass tool tests per API path.
- Imports: move non‑optional imports to module scope; keep optional provider SDK imports lazy and guarded.
- Finalize predicate: detect missing required keys recursively for object schemas to reduce parse failures; unit tests added.

### Tests & Coverage
- Added unit tests for ask context, env overrides, finalize predicate presence checks; restored async ask context test. Non‑integration coverage ≥ 80%.

## [0.3.0] - 2025-09-02
### Highlights
- Finalize centralization: one canonical rule in `should_finalize_structured_output` handles strings (including wrapped primitives) vs. non-strings. Providers defer to it; string outputs finalize only when empty.
- Shared helpers: `build_tools_common` for uniform tool-schema building; `ensure_object_schema` for wrapping primitives into `{ "value": ... }` across providers.
- Config extras normalization: generic-first keys with provider-prefixed fallbacks (`tool_choice`, `allowed_tools`, `disable_parallel_tool_use`, `ollama_api`).
- Client naming consistency: use `_get_sync_client` / `_get_async_client` in all providers; tests updated accordingly.
- Streaming cleanup: robust `close()`/`aclose()` handling for Gemini and Ollama streams; OpenAI/Anthropic already use context managers.
- Anthropic: skip JSON prefill after tool errors so plain tool messages surface; parity with OpenAI tests.
- Ollama: remove broad exception wrapping in `complete()`; runtime errors now propagate consistently.

### Docs
- Configuration guide: provider extras as tables (primary keys and fallbacks); clarified finalize behavior and streaming policy.
- Production guide: clarified error surfaces (ConfigurationError, CommandError, ToolError, ToolLoopLimitExceeded) and retry semantics.

### Tests
- Updated provider tests to patch new client getters; fixed Gemini and Ollama adapters accordingly.
- Added unit tests for `ensure_object_schema` and `build_tools_common`.

## [0.2.2] - 2025-08-29
### Highlights
- Shared tool loop: centralized control flow via `BaseLoopState` with a unified `run_tool_loop`/`arun_tool_loop`. OpenAI (Responses), Anthropic, and Gemini migrated; Gemini now always uses the shared loop regardless of tools.
- Streaming API: `ask.stream_async()` returns an `AsyncIterable[str]` directly (no await at call site), aligning with the docs and stubs.
- Structured outputs: providers perform a single finalize shot only when `auto_finalize_missing_output=True` (default remains on). Turn‑limit semantics and text‑only streaming preserved.
- OpenAI: drop temperature for reasoning models (`gpt-5`, `o1`, `o3`) and log a debug line when ignored.
- Fake backend: fills nested required properties from the schema for stricter parity with provider strict mode.

### Docs
- Added contributor note on the shared loop and `BaseLoopState` contract (Architecture → Provider Abstraction).
- Streaming guide: added a clear warning for text‑only streaming.
- Configuration: clarified provider extras (tool choice settings) and finalize behavior.

### Tests / CI
- Align test suite with design: unit, providers (SDK‑patched), integration (providers + scenarios), parity_live (serial), examples.
- Add autouse config reset fixture, `ScriptedFakeBackend`, and provider patch helper.
- Providers: OpenAI adapter tests (request/schema/stream gating, async parallel tools, finalize follow‑up, tool‑limit); parity tests for Anthropic and Gemini (tool‑limit + finalize follow‑up).
- Integration scenarios: structured outputs, minimal tool chain, text‑only streaming.
- Parity live: price extraction using typed outputs + normalization + oracle (symbol→ISO, thousands/decimal handling); remove output token cap to avoid truncation.
- Examples smoke: runs curated examples via `ALLOY_BACKEND=fake`.
- Pre‑commit: enforce top‑level `from alloy import ...` public imports in tests/docs.
- Coverage: add `pytest-cov`; `make ci-fast` enforces ≥85% coverage on fast suites.
- CI: PR workflow (fast lint/type/tests+coverage) and Nightly workflow (integration + parity live with provider keys).

### Internal / Typing
- Add Optional/Union handling in parser to support new parsing tests.
- Minor mypy and ruff cleanups in tests; remove unnecessary inline comments for clarity.

## [0.2.1] - 2025-08-26
### Fixes
- config: Prevent per-call overrides from resetting unspecified fields (e.g., `max_tool_turns`) to dataclass defaults. This fixes env/config values being ignored when commands passed only `default_system`.
- precedence: Apply per-call > configure/context > env > defaults as documented; env now acts as defaults and does not override explicit `configure(...)`.
### Internal
- config refactor: cache env parsing with lru_cache, add concise warnings for malformed env; simplify merging via dataclasses.replace and remove explicit key tracking.

### Docs/Tests
- README: clarify default `max_tool_turns=10` and precedence.
- Unit tests: add coverage to ensure overrides don’t clobber `max_tool_turns` and that configure beats env where both are set.

## [0.2.0] - 2025-08-26
### Cross‑provider
- Streaming policy unified: text‑only streaming across providers; commands with tools or non‑string outputs do not stream (enforced in code and docs).
- Default `max_tool_turns=10` (override via `configure` or `ALLOY_MAX_TOOL_TURNS`).

### OpenAI
- Migrate to Responses API; shared request builder and centralized function‑calling loop via `_LoopState`.
- Safer output assembly; always thread `previous_response_id`.
- Single follow‑up finalize (no tools) for missing structured outputs; raise `ToolLoopLimitExceeded` when turn cap exceeded.
- Async parallel tool execution using `asyncio.to_thread`.

### Gemini
- Backend refactor for non‑streaming flows: capped tool loop and strict finalize with schema.
- Text‑only streaming preserved; no tools/structured outputs in stream.

### Anthropic
- Parity with OpenAI/Gemini: robust tool loop with single user message for parallel tool results.
- Respect configured `tool_choice` (default `{type:"auto"}`) and `anthropic_disable_parallel_tool_use`.
- Structured outputs: prefill only for non‑string primitives and object schemas; no prefill for strings; JSON‑only finalization step after tools when needed.
- Text‑only streaming supported; no tools/structured outputs in stream.

### Commands & typing
- Enforce command prompt functions `-> str`; decorator controls output type.
- Clearer parse errors and refined type stubs for default returns and async.

### Tests & docs
- Anthropic integration tests for structured float/object, streaming, and parallel tool calls.
- Docs: stability, configuration defaults, and streaming policy clarified; theme/brand updates.

## [0.1.4] - 2025-08-14
- Typing: default static return type to `str` when `output` is omitted (sync → `str`, async → `Awaitable[str]`); refined decorator overloads and preserved ParamSpec. `ask.stream_async` typed as `AsyncIterable[str]`.
- DBC (Design by Contract): `ToolError` messages from `@require/@ensure` now surface back to the model as tool outputs (OpenAI/Anthropic), enabling early corrective feedback instead of hard failures. Added unit + integration tests and docs.
- Docs: new Typing page, Equivalence Guide (mapping SDK patterns → Alloy primitives), Tool Recipes (HTTP fetch, file search, provider-backed web search, DBC sequence), and examples under `examples/patterns/*`.
- Style: standardized examples to snake_case commands, bare `@command`/`@tool` when no options, and top-level imports (`from alloy import ...`).
- Tooling: pre-commit hooks to enforce top-level imports and decorator style in code and docs.

## 0.1.3 - 2025-08-11
- Structured outputs: OpenAI/Anthropic/Gemini now receive JSON Schema; primitives are wrapped and unwrapped as `{ "value": ... }`.
- Prompt shaping: Minimal guardrails appended to prompts to bias models to strict outputs for primitives and JSON for objects.
- Clearer errors: Parse failures raise `CommandError` with expected type and an output snippet.
- Ollama: Primitive outputs enforced via JSON instruction and a single follow-up attempt; tolerant unwrapping supported.
- Tests: Consolidated unit tests under `tests/unit`; kept integration tests under `tests/integration`.
- Docs: Added `docs/outputs.md` and linked from navigation; README links to the page.
- Add docs site with MkDocs + mkdocstrings
- GitHub Pages deploy workflow; docs build on PRs
- Drop legacy Gemini SDK; support google-genai only
- Bump dependencies to current sane minimums
- MIT license

## [0.1.2] - 2025-08-11
- CI: fix Ruff invocation on GitHub Actions (use `ruff check .`)
- Release: mark PyPI deployment green post-publish

## [0.1.1] - 2025-08-11
- First PyPI publish under distribution name `alloy-ai` (import remains `alloy`)
- CI: release workflow with Trusted Publishing (OIDC)
- Docs: expanded API pages, theme, and link checker

## [0.1.0] - 2025-08-10
- Initial public scaffold of Alloy (Python)
- Typed commands, ask namespace, tools
- OpenAI backend (structured outputs, tools), Anthropic, Gemini, Ollama
- Retries, streaming, env-based config, src layout, tests, CI

[Unreleased]: https://github.com/lydakis/alloy-py/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/lydakis/alloy-py/releases/tag/v0.3.1
[0.3.0]: https://github.com/lydakis/alloy-py/releases/tag/v0.3.0
[0.2.1]: https://github.com/lydakis/alloy-py/releases/tag/v0.2.1
[0.2.0]: https://github.com/lydakis/alloy-py/releases/tag/v0.2.0
[0.1.4]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.4
[0.1.3]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.3
[0.1.2]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.2
[0.1.1]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.1
[0.1.0]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.0
