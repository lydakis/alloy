# Commands & Tools

## Commands

Declare a command with `@command`. The function returns a prompt string. The decorator executes the model and parses output into the declared type.

```python
from alloy import command

@command(output=int)
def Compute() -> str:
    return "Return 6*7 as a number."

assert Compute() == 42
```

## Tools

```python
from alloy import command, tool

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@command(output=int, tools=[add])
def UseAdd() -> str:
    return "Use add(a,b) to compute 19+23. Return only the number."
```

## Ask

```python
from alloy import ask

print(ask("Explain in one sentence."))
```

## Streaming

```python
from alloy import command, ask

@command(output=str)
def Generate() -> str:
    return "Write a haiku about alloy."

# Iterate chunks (sync). For async commands, use `async for`.
for chunk in Generate.stream():
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
def Maybe() -> str:
    return "Return an integer between 1 and 10."

try:
    print(Maybe())
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
