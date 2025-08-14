# Typing

Alloy provides precise static types for commands and ask via `.pyi` stubs.

- Use `@command(output=T)` for a typed result `T`.
- If you omit `output`, the command returns `str` (and `Awaitable[str]` for async).
- Parameters are preserved (ParamSpec), so your decorated command keeps the same args.
- Streaming always yields text chunks (`str`).

Basics
```python
from alloy import command, ask

@command(output=float)
def extract_price(text: str) -> str:
    return f"Extract price from: {text}"

price: float = extract_price("the price is 5.99")

# No output → str
@command()
def summarize(text: str) -> str:
    return f"Summarize: {text}"

summary: str = summarize("hello")
```

Async
```python
from dataclasses import dataclass
from typing import Awaitable, AsyncIterable
from alloy import command

@dataclass
class User:
    name: str
    id: int

@command(output=User)
async def fetch_user(name: str) -> str:
    return f"Find user named {name} and return JSON"

user_awaitable: Awaitable[User] = fetch_user()
# after await -> User

# Streaming
chunks: AsyncIterable[str] = fetch_user.stream()

# Convenience
user_awaitable2: Awaitable[User] = fetch_user.async_()
```

Ask namespace
```python
from typing import Iterable, AsyncIterable
from alloy import ask

text: str = ask("Explain in one sentence.")
sync_stream: Iterable[str] = ask.stream("Explain briefly.")
async_stream: AsyncIterable[str] = ask.stream_async("Explain briefly.")
```

Notes
- Import from `alloy`: `from alloy import command, ask`. Importing through submodules bypasses the stubs.
- Runtime can infer output types from your prompt function’s return annotation if `output` is omitted, but static typing stays predictable: omit → `str`.
