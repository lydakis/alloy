# Contributing to Docs

- Style: Use Google-style docstrings for public functions, classes, and modules.
- Local preview: `pip install -e '.[docs]'` then `make docs-serve`.
- Build check: `make docs-build` (uses `--strict`).
- PRs: Docs workflow builds for pull requests; deploy happens only on `main`.

## Style (Project Conventions)

- Naming: snake_case for functions/commands/tools; PascalCase for classes/dataclasses.
- Decorators: use bare `@command`/`@tool` when no options; use `@command(...)`/`@tool(...)` when passing options.
- Typing: prefer `@command(output=T)` for precise static types; when `output` is omitted, static return is `str` (async → `Awaitable[str]`).
- Imports: prefer top-level `from alloy import ...` (stubs apply), not submodules like `from alloy.tool import tool`.
- Docstrings: concise, imperative summaries; short examples with snake_case.

## Docstring example (Google style)

```python
def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
      a: First number.
      b: Second number.

    Returns:
      The sum of a and b.
    """
    return a + b
```
