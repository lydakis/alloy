# Getting Started

## Install

- All providers: `pip install "alloy-ai[providers]"`
- Minimal (OpenAI only): `pip install alloy-ai`

Optional: `pip install -e '.[providers]'` to work on the repo in editable mode.

## Configure credentials

Create a `.env` in your project root:

```
OPENAI_API_KEY=sk-...
```

Optionally set `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY` for other providers.

## First command

```python
from alloy import command, ask
from dotenv import load_dotenv

load_dotenv()

@command(output=float)
def extract_price(text: str) -> str:
    """Extract price from text."""
    return f"Extract the price (number only) from: {text}"

print(extract_price("This item costs $49.99."))
print(ask("Say OK in one word."))
```

## Progressive path

Start small and add structure as needed:

1) Explore: `ask("...")`

2) Command returning text:
```python
@command
def draft() -> str:
    return "Write a short haiku about alloy."
```

3) Enforce types:
```python
@command(output=float)
def extract_price(text: str) -> str:
    return f"Extract the price (number only) from: {text}"
```

4) Add tools + contracts:
```python
@tool
@require(lambda ba: ba.arguments.get("x", 0) >= 0, "x must be non-negative")
def sqrt_floor(x: int) -> int: ...

@command(output=int, tools=[sqrt_floor])
def compute() -> str:
    return "Use sqrt_floor(x) for x=49 and return the number only."
```

Streaming
- For responsiveness, text-only commands can stream: `for chunk in draft.stream(): ...`.
- Commands with tools or non‑string outputs do not stream; call them normally to get a typed result.
