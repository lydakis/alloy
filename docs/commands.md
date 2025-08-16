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

## Sync, async, and streaming

Commands can run synchronously or asynchronously. Define an `async def`
function to build an async command. Both sync and async commands expose
`.async_()` for asynchronous invocation and `.stream()` for streaming
output.

```python
from alloy import command

# Sync command
@command(output=str)
def generate() -> str:
    return "Write a haiku about alloy."

print(generate())  # sync result
print(await generate.async_())  # run sync command asynchronously

# Async command
@command(output=str)
async def agen() -> str:
    return "Write a haiku about alloy."

print(await agen())  # async result

# Streaming output
for chunk in generate.stream():
    print(chunk, end="")

async for chunk in agen.stream():
    print(chunk, end="")
```

Sync commands expose `.async_()` so they can participate in `asyncio`
workflows, for example `await asyncio.gather(generate.async_(), agen())`.

The `ask` helper mirrors these modalities via `ask()`, `await ask.async_(...)`,
`ask.stream(...)`, and `ask.stream_async(...)`.

## Retries and error handling

```python
from alloy import command, configure, CommandError

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
@require(lambda ba: ba.arguments.get("x", 0) >= 0, "x must be non-negative")
@ensure(lambda r: r >= 0, "result must be non-negative")
def sqrt_floor(x: int) -> int:
    """Return floor(sqrt(x))."""
    import math
    return int(math.sqrt(x))
```

Design by Contract (DBC)
- `@require` runs before the tool; it receives bound arguments (`inspect.BoundArguments`).
- `@ensure` runs after the tool; it receives the tool's result.
- Predicates may run arbitrary checks; return truthy to allow, falsy to block.
- On failure, Alloy surfaces the contract message back to the model as the tool output, not a hard exception, so the model can adjust (e.g., call a prerequisite or pass different args).

Decorator order
- Place `@tool` above `@require/@ensure` so contracts attach to the underlying function first:

```python
@tool
@require(...)
@ensure(...)
def my_tool(...): ...
```

Tips
- Keep messages short and instructive ("x must be non-negative").
- Validate presence and shape of args in `@require`; validate effects/invariants in `@ensure`.
- For non-contract runtime failures, raise an exception; Alloy will pass a brief error message back to the model.
