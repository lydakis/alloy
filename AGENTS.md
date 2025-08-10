# Repository Guidelines

## Project Structure & Module Organization
- `alloy/`: Core library.
  - `ask.py`, `command.py`, `tool.py`: Prompt, command, and tool orchestration.
  - `config.py`, `types.py`, `errors.py`: Configuration, shared types, errors.
  - `models/`: Model adapters (`base.py`, `openai.py`). Put provider‑specific code here.
- `examples/`: Runnable scripts (`basic_usage.py`, `tools_demo.py`).
- `alloy-spec-v1.md`: Reference spec for behaviors and interfaces.
- `.env`: Local secrets (e.g., `OPENAI_API_KEY`). Do not commit.

## Build, Test, and Development Commands
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install openai python-dotenv`
- Run examples: `python examples/basic_usage.py` or `python examples/tools_demo.py`.
- Lint/format (optional): `ruff .` and `black .` if you use them.

## Coding Style & Naming Conventions
- Indentation: 4 spaces; follow PEP 8 + type hints.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Docstrings: Use concise, imperative summaries. Include argument/return types when non‑obvious.
- Public API: Re‑export only stable symbols in `alloy/__init__.py`.
- Models: Keep provider‑agnostic logic outside `models/`; implement providers under `alloy/models/<provider>.py`.

## Testing Guidelines
- Framework: Prefer `pytest`.
- Layout: `tests/` mirroring package modules; files named `test_*.py`.
- Running: `pytest -q` (add `-k pattern` to filter).
- Coverage (target): Aim for meaningful tests around prompts/contracts and model adapters; include edge cases for parsing/validation.

## Commit & Pull Request Guidelines
- Commits: Use imperative mood; consider Conventional Commits (e.g., `feat:`, `fix:`, `docs:`) for clarity.
- Scope small, message specific: what/why over how.
- PRs: Include description, rationale, and screenshots/console snippets if behavior changes. Link related issues. Note any breaking changes.
- Checks: Ensure examples run (`examples/*.py`) and no regressions in public API.

## Security & Configuration Tips
- Secrets: Keep `OPENAI_API_KEY` in `.env` locally; never commit secrets.
- Fail‑safe defaults: Validate config in `config.py`; handle missing keys with clear errors.
