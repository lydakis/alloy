# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to
Semantic Versioning.

## [Unreleased]

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

[Unreleased]: https://github.com/lydakis/alloy-py/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.2
[0.1.1]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.1
[0.1.0]: https://github.com/lydakis/alloy-py/releases/tag/v0.1.0
