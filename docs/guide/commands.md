# Commands

Audience: developers authoring Alloy commands and choosing signatures.
Outcome: know how to declare commands, set `output`, use sync/async/streaming, and handle errors.
Time: 7 minutes
Prereqs: Python 3.10+, `pip install alloy-ai`.

---

## Declaration and return discipline

- The decorated function returns a prompt `str`.
- The decorator’s `output` parameter controls the command’s actual return type.

```python
from alloy import command

@command                  # returns str
def text_gen(topic: str) -> str:
    return f"Write a one-liner about: {topic}"

@command(output=int)      # returns int
def number() -> str:
    return "Return 6*7 as a number."
```

Why this shape: predictable typing in Python, explicit control of the model result type, and clear error surfaces when the provider cannot produce the requested type.

## Sync, async, and streaming

Use sync or async functions. Both expose `.async_()` and `.stream()` helpers.

```python
from alloy import command

@command(output=str)
def gen() -> str:
    return "Write a haiku about alloy."

print(gen())                  # sync
print(await gen.async_())     # async invocation of sync command

@command(output=str)
async def agen() -> str:
    return "Write a haiku about alloy."

print(await agen())

for chunk in gen.stream():
    print(chunk, end="")

async for chunk in agen.stream():
    print(chunk, end="")
```

Streaming policy (canonical): see Guide → Streaming.

## Error surfaces and retries

- `CommandError`: model didn’t produce a final output or failed to parse into the requested type.
- `ConfigurationError`: invalid `output` shape or unsupported strict schema.
- Retries: `configure(retry=...)` or per‑call override.

```python
from alloy import command, configure, CommandError

configure(retry=2)

@command(output=int)
def maybe() -> str:
    return "Return an integer between 1 and 10."

try:
    print(maybe())
except CommandError as e:
    print("Model error:", e)
```

## Tools and contracts

Attach tools to a command to use your local capabilities. See Guide → Tools & Workflows and Guide → Contracts.
