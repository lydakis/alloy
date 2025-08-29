# Common Pitfalls

Short, fixable patterns that improve reliability and DX.

## Freeform text vs typed outputs

Wrong
```python
from alloy import command

@command
def summarize(text: str) -> dict:  # wrong: annotation suggests dict
    return f"Summarize: {text}"
```

Right
```python
from alloy import command

@command  # returns str by default
def summarize(text: str) -> str:
    return f"Summarize: {text}"
```

To get a typed result, declare it explicitly:
```python
from dataclasses import dataclass
from alloy import command

@dataclass
class Article:
    title: str
    points: list[str]

@command(output=Article)
def extract(text: str) -> str:
    return f"Return: title + 3–5 points. Text: {text}"
```

## Streaming limits

- Streaming is text‑only today.
- Commands with tools or typed outputs do not stream — call them normally to get the final typed result.

Wrong
```python
for item in cmd.stream(...):  # cmd returns list[Article]
    ...
```

Right
```python
items = cmd(...)
```

See: Guide → Streaming.

## Dict outputs in strict mode

- Open‑ended dict outputs are not supported under strict JSON Schema.
- Use a concrete schema: `@dataclass` or `TypedDict`.

Wrong
```python
@command(output=dict)
def info() -> str:
    return "Return any JSON object"
```

Right
```python
from typing import TypedDict

class Info(TypedDict):
    summary: str
    score: int

@command(output=Info)
def info() -> str:
    return "Return {summary, score}"
```

Note
- Dicts are allowed as tool input parameters. Tool schemas are non‑strict and accept open‑ended objects for inputs, while outputs remain strict.

## Tool loop limits

- The tool loop is capped by `max_tool_turns` (default 10) to avoid runaway behavior.
- Raise or return contract messages to guide recovery.

```python
from alloy import require, ensure, tool, configure

configure(max_tool_turns=10)

@tool
@require(lambda ba: ba.arguments.get("x", 0) >= 0, "x must be non-negative")
@ensure(lambda r: r >= 0, "result must be non-negative")
def sqrt_floor(x: int) -> int:
    import math
    return int(math.sqrt(x))
```

## Picking a provider

- `ALLOY_MODEL` determines the provider: `gpt-5-mini`, `claude-…`, `gemini-…`, `ollama:<model>`.
- Use `ALLOY_BACKEND=fake` only for offline demos and tests.

Quick start
```bash
export OPENAI_API_KEY=...
export ALLOY_MODEL=gpt-5-mini
```
