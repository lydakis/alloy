# Core Concepts

Audience: developers new to Alloy evaluating the model and API fit.
Outcome: understand Commands, Tools, Types, Contracts, and Providers with a minimal snippet for each.
Time: 5 minutes
Prereqs: Python 3.10+, `pip install alloy-ai`.

---

## Commands

Commands are Python functions decorated with `@command`. The function returns the prompt `str`; the decorator runs the model and returns a value according to `output`.

```python
from alloy import command

@command  # returns str by default
def summarize(text: str) -> str:
    return f"Summarize succinctly: {text}"

print(summarize("Alloy lets you write typed AI functions."))
```

## Tools

Tools are plain Python functions decorated with `@tool` that a command can call to use your local capabilities.

```python
from alloy import command, tool

@tool
def add(a: int, b: int) -> int:
    return a + b

@command(output=int, tools=[add])
def compute() -> str:
    return "Use add(a,b) to compute 19+23. Return only the number."
```

## Types (structured outputs)

Ask the model for a concrete Python type; Alloy enforces the schema with provider‑native structured outputs.

```python
from dataclasses import dataclass
from alloy import command

@dataclass
class ArticleSummary:
    title: str
    key_points: list[str]

@command(output=ArticleSummary)
def summarize_article(text: str) -> str:
    return f"Summarize with title and 3–5 key_points. Article: {text}"
```

See: Guide → Structured Outputs.

## Contracts (require/ensure)

Design‑by‑contract around tools to keep workflows safe and explicit.

```python
from alloy import tool, require, ensure

@tool
@require(lambda ba: ba.arguments.get("x", 0) >= 0, "x must be non-negative")
@ensure(lambda r: r >= 0, "result must be non-negative")
def sqrt_floor(x: int) -> int:
    import math
    return int(math.sqrt(x))
```

## Providers

Use any supported provider by setting the model ID and API key — no code changes.

```bash
export OPENAI_API_KEY=...
export ALLOY_MODEL=gpt-5-mini
# Offline demos only: export ALLOY_BACKEND=fake
```

See: Guide → Providers (setup + capability matrix).
