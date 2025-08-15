# Commands & Tools

## Commands

Declare a command with `@command`. The function returns a prompt string. The decorator executes the model and parses output into the declared type.

Style: prefer snake_case names for commands and tools (PEP 8). Use PascalCase for classes/dataclasses. Use bare `@command`/`@tool` when no options; use `@command(...)`/`@tool(...)` when passing options.

Typing: when `output` is omitted, the command returns `str` (or `Awaitable[str]` for async). With `output=T`, calls return `T` (or `Awaitable[T]` for async), `.stream()` yields `str` chunks, and `.async_()` awaits to `T`.

```python
from alloy import command

@command(output=int)
def compute() -> str:
    return "Return 6*7 as a number."

assert compute() == 42
```

## Tools

```python
from alloy import command, tool

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@command(output=int, tools=[add])
def use_add() -> str:
    return "Use add(a,b) to compute 19+23. Return only the number."
```

See also: Tool Recipes for minimal, copy‑pasteable examples (HTTP fetch, local file search, dev‑only Python exec).

## Ask

```python
from alloy import ask

print(ask("Explain in one sentence."))
```

## Streaming

```python
from alloy import command, ask

@command(output=str)
def generate() -> str:
    return "Write a haiku about alloy."

# Iterate chunks (sync). For async commands, use `async for`.
for chunk in generate.stream():
    print(chunk, end="")

for chunk in ask.stream("Explain briefly."):
    print(chunk, end="")
```

## Retries and error handling

```python
from alloy import command, configure
from alloy.errors import CommandError

# Global defaults
configure(retry=2)  # retry transient errors twice

@command(output=int)
def maybe() -> str:
    return "Return an integer between 1 and 10."

try:
    print(maybe())
except CommandError as e:
    print("Model error:", e)
```

## Contracts (require/ensure)

```python
from alloy import tool, require, ensure

@tool
@require(lambda x: x >= 0, "x must be non-negative")
@ensure(lambda r: r >= 0, "result must be non-negative")
def sqrt_floor(x: int) -> int:
    """Return floor(sqrt(x))."""
    import math
    return int(math.sqrt(x))
```
