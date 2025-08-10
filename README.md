Alloy (Python): Python for logic. English for intelligence.

This repository contains an early scaffold of the Alloy library per `alloy-spec-v1.md`.

Quick start
- Install: `pip install openai python-dotenv`
- Create `.env` with `OPENAI_API_KEY=...`
- Use the API:

```python
from dataclasses import dataclass
from dotenv import load_dotenv
from alloy import command, ask, configure

load_dotenv()
# Optional: configure() — default model is `gpt-5-mini` if omitted
# configure(model="gpt-5", temperature=0.7)

@command(output=float)
def ExtractPrice(text: str) -> str:
    """Extract price from text."""
    return f"Extract the price (number only) from: {text}"

print(ExtractPrice("This item costs $49.99."))
print(ask("Say hi"))
```

Notes
- OpenAI backend is implemented for sync/async/streaming.
- Streaming with tools is not yet supported.
- For structured outputs, Alloy attempts to use OpenAI structured responses (JSON schema). If unavailable, the model may still return JSON, which Alloy parses best-effort.

Examples
- See `examples/basic_usage.py` and `examples/tools_demo.py` (tools + contracts).

How to run locally
- `pip install openai python-dotenv`
- Create `.env` with `OPENAI_API_KEY=...`
- Option A (no install):
  - `python examples/basic_usage.py`
  - `python examples/tools_demo.py`
  - (examples add `src/` to `sys.path` for you)
- Option B (editable install):
  - `pip install -e .`
  - Then run from anywhere.

.env example
```
OPENAI_API_KEY=sk-...
```
