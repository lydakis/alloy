# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to
Semantic Versioning.

## [Unreleased]

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

[Unreleased]: https://github.com/lydakis/alloy-py/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/lydakis/alloy-py/releases/tag/v0.2.1
[0.2.0]: https://github.com/lydakis/alloy-py/releases/tag/v0.2.0
[0.1.4]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.4
[0.1.3]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.3
[0.1.2]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.2
[0.1.1]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.1
[0.1.0]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.0
