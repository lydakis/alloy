# Contributing to Docs

- Style: Use Google-style docstrings for public functions, classes, and modules.
- Local preview: `pip install -e '.[docs]'` then `make docs-serve`.
- Build check: `make docs-build` (uses `--strict`).
- PRs: Docs workflow builds for pull requests; deploy happens only on `main`.

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

