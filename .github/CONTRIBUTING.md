# Contributing to alloy-py

Thanks for helping improve Alloy (Python)! This doc is intentionally concise so you can get productive fast.

## Quick Start
- Create env: `python -m venv .venv && source .venv/bin/activate`
- Install dev deps: `pip install -e '.[dev]'`
- Install hooks: `pre-commit install`
- Run checks locally:
  - Lint: `ruff check .` and `black --check .`
  - Types: `mypy .`
  - Tests: `pytest -q`

## Expectations & Scope
- Maintainer-led: direction and final decisions rest with @lydakis. No SLA.
- Gift exchange: contributions are welcomed when they fit the project’s scope and maintenance budget.
- Build-for-use: features not used by the maintainer usually won’t merge unless someone commits to maintain them.

## Project Conventions
- Style: PEP 8, 4 spaces, type hints everywhere practical.
- Naming: `snake_case` (functions/vars), `PascalCase` (classes), `UPPER_SNAKE_CASE` (constants).
- Public API: import via `from alloy import ...` only; keep re-exports curated in `alloy/__init__.py`.
- Decorators: use bare `@command`/`@tool` when no options; otherwise `@command(...)`/`@tool(...)`.
- Models: provider-agnostic logic in `alloy/*`; provider adapters live in `alloy/models/<provider>.py`.

## Tests
- Run unit tests: `pytest -q`
- Filter: `pytest -q -k pattern`
- Integration tests (optional): set provider keys, then run `pytest -q tests/integration`
  - OpenAI: `OPENAI_API_KEY`
  - Anthropic: `ANTHROPIC_API_KEY`
  - Gemini: `GOOGLE_API_KEY`
  - Model: `ALLOY_IT_MODEL` (e.g., `gpt-5-mini`, `claude-*`, `gemini-*`, or `ollama:<name>`)
  - To skip provider integ tests locally: `ALLOY_IT_MODEL=none pytest -q`

## Pull Requests
- Keep PRs scoped and focused; include what/why in the description.
- Checklist:
  - [ ] Lint and format pass (`ruff`, `black`)
  - [ ] Types pass (`mypy`)
  - [ ] Tests added/updated and passing (`pytest`)
  - [ ] Docs updated if behavior or public API changed
- Commits: imperative mood; Conventional Commits style welcome (e.g., `feat:`, `fix:`, `docs:`).
- Discussions and design: keep decisions public where possible (issues/PR discussion).

Getting merged
- Align with scope and direction (see Philosophy and Governance docs).
- Keep changes minimal with clear tests and docs.
- If the maintainers don’t use the feature, propose a plan to maintain it long-term.

## Security
- Do not include secrets in issues/PRs. See `.github/SECURITY.md` for private reporting.

## Getting Help
- Check `README.md`, `alloy-spec-v1.md`, `examples/`, and `docs/`.
- If unsure, open a draft PR or start a discussion with your approach.

References
- Project stance: see README.md (Maintainer-led, gift-exchange, scope)
- Code of Conduct: `.github/CODE_OF_CONDUCT.md`

Thanks again for contributing!
