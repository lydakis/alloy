# Alloy (Python)

Python for logic. English for intelligence.

!!! success "Outcomes first"
    - Run your first command in under 2 minutes.
    - Enforce typed outputs without brittle parsing.
    - Add tools + contracts safely.
    - Switch providers without code changes.

## What is Alloy?

Alloy lets you write typed AI functions that feel like normal Python. Decorate a function with `@command`, optionally declare `output=T`, and Alloy enforces the result via provider‑native structured outputs. Add plain‑Python tools (`@tool`) with [design‑by‑contract](guide/contracts.md) to keep workflows reliable. Switch providers by changing environment variables — no code changes.

> What Alloy is / isn’t: see the concise guide in [Equivalence](equivalence.md).

## Quick Start

Install
```bash
pip install alloy-ai
```

Set a provider (OpenAI example)
```bash
export OPENAI_API_KEY=...
export ALLOY_MODEL=gpt-5-mini
# Offline demos: export ALLOY_BACKEND=fake
```

Write code
```python
from alloy import command

@command
def summarize(text: str) -> str:
    """Return a short summary of the input."""

print(summarize("Alloy lets you write typed AI functions in plain Python."))
# → "Write typed AI functions in plain Python."
```

Links: [Tutorial](tutorial/index.md) · [Guide](guide/core-concepts.md) · [Examples](examples/index.md) · [Providers](guide/providers.md) · [What’s New](whats-new.md)

## Streaming

Current: text streaming, and tool-calling can also stream text on supported backends (OpenAI/Anthropic/Gemini today). Non-string outputs do not stream yet. See [Guide → Streaming](guide/streaming.md).

Preview (vNext): structured output streaming as full objects is planned, not yet available.

## Providers

Model IDs and capabilities evolve. The Providers page maintains the up‑to‑date capability matrix and setup steps per provider: [Guide → Providers](guide/providers.md).
