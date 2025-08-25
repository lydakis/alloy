# Alloy Roadmap

This page outlines the planned work for Alloy. It captures themes and release-sized milestones. Day-to-day tasks are tracked in GitHub Issues and grouped under Milestones.

- Source of truth: this document (high-level) + GitHub Issues/Milestones (detailed).
- Versioning: pre-1.0 semantic versioning. New features bump the minor version; fixes bump patch.

## Themes

- Provider parity: close feature gaps across OpenAI, Anthropic, Gemini, and Ollama.
- Structured outputs: robust, typed outputs for primitives, collections, dataclasses, TypedDict, and (opt-in) Pydantic.
- Tooling & reasoning: native tool use where supported; ReAct fallback for others.
- Performance & reliability: sensible defaults, retries/backoff, and efficient client reuse.
- Developer experience: strong type stubs, docs, examples, and contribution workflow.
- Testing: unit-first with fake backends; guarded integration tests per provider.

## Milestones

### v0.2 – Type Safety & Tool Schema

- Improve type stubs
  - Add a `Protocol` for decorated commands exposing `__call__`, `.stream()`, and `.async_()` so IDEs/type-checkers know about these methods.
  - Tighten `ask.stream_async` return type to `AsyncIterable[str]` in `.pyi`.
- Tool schema fidelity
  - Generate JSON schema from Python type hints and defaults (str/int/float/bool, Optional/Union, dataclasses), not just `"string"` placeholders.
  - Mark optional vs required based on defaults; include simple nested objects.
- Tests
  - Add unit tests for `@require`/`@ensure` contract failures.
  - Add tests for `TypedDict` parsing and common generics (list[TypedDict], dict[str, int]).
- Docs
  - Document stub behavior and how `.stream()`/`.async_()` type as part of the decorated command object.

### v0.3 – ReAct Fallback & Streaming (Simplified)

- ReAct fallback
  - Implement minimal ReAct loop for models without native tool/function calling.
  - Safety: max turns, clear termination, and error surfacing.
  - Routing: fallback path for providers lacking native tools.
- Streaming
  - Align providers on text-only streaming: no tools, no structured outputs.
  - Keep `.stream()` as a simple text delta iterator; document using provider SDKs directly for complex streaming.

### v0.4 – Structured Outputs Beyond Dataclasses

- TypedDict: add schema and parsing support equivalent to dataclasses.
- Pydantic (opt-in): parse to models (v1/v2 detection); feature-flag behind an extra.
- Parser hooks: allow custom parsers for project-specific types.

### v0.5 – Provider Parity & Performance

- Gemini: implement native tool-calling where supported by the SDK.
- Streaming parity: ensure text-only streaming consistency across providers.
- Client/session reuse: cache SDK clients per backend to reduce per-call overhead while keeping thread/process safety.
- Reliability: add exponential backoff with jitter on retryable failures (configurable).

### v0.6 – DX, Docs, and CI Polish

- Contributing
  - Add `CONTRIBUTING.md` and issue/PR templates.
  - Clarify release process and versioning policy.
- Examples & docs
  - Expand examples (e.g., notebook walkthrough, expected outcomes section).
  - Auto-generate/maintain feature support matrix from code/tests.
- CI
  - Add coverage reporting; keep unit/integration split and gating for provider keys.

### v0.7 – Observability (Planned)

- OpenTelemetry spans for commands, backend calls, tools, and parsing (optional and off by default).
- Export to common backends (OTLP/HTTP); keep provider-agnostic and minimal overhead.

### v1.0 – Stability & API Freeze

- Finalize API shapes for commands, tools, config, and backends.
- Ensure provider parity meets documented support matrix.
- Remove temporary or deprecated shims; lock public surface in `__all__` and `.pyi`.

## Incorporating Review Feedback

- Performance
  - Keep overhead minimal; prioritize provider-side JSON schema and light parsing.
  - Reuse provider clients across calls (micro-optimization) without holding brittle global state.
  - Watch large JSON parsing costs; add note and guidance for chunked/streaming scenarios.
- Code quality
  - Reduce sync/async duplication in backends by extracting shared helpers for tool loops and schema wrapping.
  - Maintain clear error messages (parsing failures with context snippets).
- Testing
  - Strengthen contract tests and edge cases around retries and parsing.
  - Keep integration tests guarded by secrets; assert types/ranges rather than exact text.
- Documentation & examples
  - Add outcome notes to examples; keep offline/dev tips like `ALLOY_BACKEND=fake`.
  - Expand contribution guidance and roadmap visibility.

## Tracking & Process

- Issues & Milestones: create GitHub milestones for each version above and group issues accordingly.
- Labels: `provider/openai`, `provider/anthropic`, `provider/gemini`, `provider/ollama`, `type-system`, `tools`, `react`, `performance`, `docs`, `tests`.
- Release notes: summarize changes by theme and link to issues/PRs.
