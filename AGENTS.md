# AGENTS — Quick Guide

This file guides coding agents working in this repository. It applies to the entire repo. Deeper `AGENTS.md` files may further specialize instructions and take precedence within their subtrees.

## Scope & Expectations
- Keep changes minimal, focused, and reversible; avoid broad refactors.
- Do not alter public API without explicit instruction; prefer additive changes.
- Never commit secrets (`.env`, API keys). Verify `.gitignore` is respected.
- Follow style tools; let formatters fix whitespace vs. hand edits.

## One‑Time Setup
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install dev deps: `pip install -e '.[dev]'`
- Install hooks: `pre-commit install`

## Core Commands
- Quick check: `make ci-fast` (lint + typecheck + focused tests, coverage >= 80)
- Full local CI: `make ci` (lint, typecheck, tests)
- Tests: `make test` (filter: `pytest -k <pattern> -q`)
- Lint/format: `make lint` / `make format` then `make precommit`
- Typecheck: `make typecheck`
- Examples (fake backend): `make examples-quick`
- Provider examples (need keys): `make examples-openai|anthropic|gemini|ollama`
- Docs: `make docs-serve` (live) or `make docs-build` (strict)
- Release (trusted publishing): create and push a tag, see `make release`

## Testing Profiles
- Unit/contracts/providers: `make ci-fast`
- Integration (requires keys): `make itest` or provider‑specific `make itest-openai|anthropic|gemini|ollama`
- Skip integ locally: `ALLOY_IT_MODEL=none pytest -q`
- Smoke examples without keys: `make smoke-examples` (uses `ALLOY_BACKEND=fake`)

## Environment Cheatsheet
- Default model: `gpt-5-mini` (override with `ALLOY_MODEL`)
- Useful vars: `ALLOY_TEMPERATURE`, `ALLOY_MAX_TOKENS`, `ALLOY_SYSTEM`/`ALLOY_DEFAULT_SYSTEM`, `ALLOY_RETRY`, `ALLOY_MAX_TOOL_TURNS`, `ALLOY_EXTRA_JSON`
- Provider keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`; use `.env` locally and `dotenv -f .env run -- <cmd>`

## Code & Docs Style
- Python: PEP 8 + type hints; 4‑space indent. Run `ruff` and `black`.
- Docstrings: concise, imperative; include non‑obvious types.
- Imports: re‑export public API from `alloy/__init__.py`; import via `from alloy import ...` in code/docs.
- Decorators: bare `@command`/`@tool` when no options; `@command(...)`/`@tool(...)` when passing options.

## Design Notes
- Provider‑agnostic logic lives outside `alloy/models/`; provider adapters go in `alloy/models/<provider>.py`.
- Tools: prefer Design‑by‑Contract via `@require`/`@ensure`; raise `ToolError` with short, instructive messages.
- Streaming: text‑only; commands with tools or non‑string outputs do not stream.

## Agent Do/Don’t
- Do: use `rg` for fast search; keep diffs tight; update docs/tests when touching behavior.
- Do: run `make precommit` before proposing a PR.
- Don’t: bump dependencies or change public symbols to satisfy lint without discussion.
- Don’t: introduce provider‑specific behavior into core modules.

---

# Repository Guidelines

## Project Structure & Module Organization
- `src/alloy/`: Core library.
  - `ask.py`, `command.py`, `tool.py`: Prompt, command, and tool orchestration.
  - `config.py`, `types.py`, `errors.py`: Configuration, shared types, errors.
  - `models/`: Model adapters (`base.py`, `openai.py`, `anthropic.py`, `gemini.py`, `ollama.py`). Put provider‑specific code here.
- `examples/`: Runnable scripts (`basic_usage.py`, `tools_demo.py`).
- `alloy-spec-v1.md`: Reference spec for behaviors and interfaces.
- `.env`: Local secrets (e.g., `OPENAI_API_KEY`). Do not commit.
- `.venv/`: Local virtual environment (git‑ignored). Do not commit.

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install dev deps (editable): `pip install -e '.[dev]'`
- Pre-commit: `pre-commit install` then `make precommit` (enforces imports and decorator style in code + docs)
- Run examples: `python examples/basic_usage.py` or `python examples/tools_demo.py` (more under `examples/patterns/`)
  - Streaming (text‑only): `python examples/basic/streaming_outputs.py`
- Lint/format: `ruff .` and `black .`
  - Without installing the package, examples/tests add `src/` to `sys.path` for convenience.

Defaults: The global config uses `model="gpt-5-mini"` so you can call `ask(...)` and commands without `configure(...)`. Use `configure(...)` to override.
Streaming is text‑only across providers; commands with tools or non‑string outputs do not stream.

## Coding Style & Naming Conventions
- Indentation: 4 spaces; follow PEP 8 + type hints.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Docstrings: Use concise, imperative summaries. Include argument/return types when non‑obvious.
- Public API: Re‑export only stable symbols in `alloy/__init__.py`; import public symbols via `from alloy import ...` (not submodules) in code and docs.
- Decorators: use bare `@command`/`@tool` when no options; use `@command(...)`/`@tool(...)` when passing options.
- Models: Keep provider‑agnostic logic outside `models/`; implement providers under `alloy/models/<provider>.py`.

## Typing & Stubs
- Default static return type for commands when `output` is omitted: sync → `str`, async → `Awaitable[str]`.
- With `output=T`, calls return `T` (async → `Awaitable[T]`); `.stream()` yields `str` chunks; `.async_()` awaits to `T`.
- `ask.stream_async(...)` is typed as `AsyncIterable[str]`.
- ParamSpec preserves prompt function parameters on the wrapped command.

## Testing Guidelines
- Framework: Prefer `pytest`.
- Layout: `tests/` mirroring package modules; files named `test_*.py`.
- Running: `pytest -q` (add `-k pattern` to filter).
- Integration tests: require real API keys and model selection via env.
  - OpenAI: set `OPENAI_API_KEY` (optional `ALLOY_IT_MODEL`, default `gpt-5-mini`).
  - Anthropic: set `ANTHROPIC_API_KEY` (and `ALLOY_IT_MODEL=claude-*`).
  - Gemini: set `GOOGLE_API_KEY` (and `ALLOY_IT_MODEL=gemini-*`).
  - Ollama: run a local Ollama instance (and `ALLOY_IT_MODEL=ollama:<name>`).
  - To skip provider integ tests locally: `ALLOY_IT_MODEL=none pytest -q`.
- Coverage (target): Aim for meaningful tests around prompts/contracts and model adapters; include edge cases for parsing/validation.

## Commit & Pull Request Guidelines
- Commits: Use imperative mood; consider Conventional Commits (e.g., `feat:`, `fix:`, `docs:`) for clarity.
- Scope small, message specific: what/why over how.
- PRs: Include description, rationale, and screenshots/console snippets if behavior changes. Link related issues. Note any breaking changes.
- Checks: Ensure examples run (`examples/*.py`) and no regressions in public API.

## Security & Configuration Tips
- Secrets: Keep `OPENAI_API_KEY` in `.env` locally; never commit secrets.
- Git ignore: Ensure `.env` and `.venv/` are ignored (they are in this repo). Never publish them.
- Fail‑safe defaults: Validate config in `config.py`; handle missing keys with clear errors.
- Environment overrides: You can set process env vars to avoid code changes: `ALLOY_MODEL`, `ALLOY_TEMPERATURE`, `ALLOY_MAX_TOKENS`, `ALLOY_SYSTEM`/`ALLOY_DEFAULT_SYSTEM`, `ALLOY_RETRY`, `ALLOY_MAX_TOOL_TURNS`, `ALLOY_EXTRA_JSON` (provider‑specific extras). Example: `export ALLOY_MODEL=gpt-5-mini`.
  - Default `max_tool_turns` is 10; increase if your workflows require more tool rounds.
  - Anthropic extras: `anthropic_tool_choice` (e.g., `{ "type": "auto"|"any"|"tool"|"none" }`), `anthropic_disable_parallel_tool_use` (bool).
 - Local runs: Use the `dotenv` CLI to load `.env` (e.g., `dotenv -f .env run -- pytest`). In CI, configure provider API keys as encrypted secrets and pass via environment variables (do not store keys in the repo).

## Design by Contract (DBC) for Tools
- Use `@require(predicate, message)` to validate preconditions (receives `inspect.BoundArguments`).
- Use `@ensure(predicate, message)` to validate postconditions (receives the tool result).
- On failure, raise a `ToolError` message back to the model: OpenAI/Anthropic backends surface this as the tool output so the model can adjust (instead of a hard failure).
- Keep messages short and instructive (e.g., "run validate_data first", "must be even").

## Streaming Policy
- Streaming is text‑only for all providers.
- Commands with tools or non‑string outputs do not stream; call them normally to get a typed result.

## Docs & Examples
- Docs pages: Typing, Equivalence Guide, Tool Recipes (HTTP fetch, file search, provider‑backed web search, DBC sequence).
- Examples: see `examples/basic_*.py`, `examples/tools_demo.py`, `examples/basic/streaming_outputs.py`, and `examples/patterns/*` for orchestration patterns expressed via commands/tools.

## Release
- Version in `pyproject.toml`; bump with changelog entries.
- Trusted Publishing: tag and push (e.g., `git tag v0.2.0 && git push origin v0.2.0`) to publish to PyPI via CI.
