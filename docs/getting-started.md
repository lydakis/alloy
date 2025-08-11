# Getting Started

## Install

- All providers: `pip install "alloy[providers]"`
- Minimal (OpenAI only): `pip install alloy`

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
def ExtractPrice(text: str) -> str:
    """Extract price from text."""
    return f"Extract the price (number only) from: {text}"

print(ExtractPrice("This item costs $49.99."))
print(ask("Say OK in one word."))
```

