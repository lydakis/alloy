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
- Environment overrides: You can set process env vars to avoid code changes: `ALLOY_MODEL`, `ALLOY_TEMPERATURE`, `ALLOY_MAX_TOKENS`, `ALLOY_SYSTEM`/`ALLOY_DEFAULT_SYSTEM`, `ALLOY_RETRY`, `ALLOY_MAX_TOOL_TURNS`, `ALLOY_EXTRA_JSON` (provider‑specific extras). Example: `export ALLOY_MODEL=gpt-4o`.
  - Default `max_tool_turns` is 2; increase if your workflows require more tool rounds.
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
