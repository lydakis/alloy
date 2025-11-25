# Streaming

Understand current text‑only streaming and the preview for sequence‑of‑objects (~4 minutes). Requires Python 3.10+ and `pip install alloy-ai`.

---

## Current (stable)

- Text-only streaming.
- Tools can stream when the configured backend advertises support (OpenAI Responses, Anthropic Claude, and Google Gemini today); otherwise the call falls back to a configuration error.

> Warning: Structured outputs are not supported while streaming. Tool streaming is limited to backends that explicitly support it.

APIs
```python
from alloy import ask, command

@command
def brainstorm(topic: str) -> str:
    return f"Write a short riff about: {topic}"

for chunk in ask.stream("Write a one-liner about cats"):
    print(chunk, end="")

for chunk in brainstorm.stream("Alloy examples"):
    print(chunk, end="")
```

Provider guidance: consult the Providers matrix for which models support text streaming.

---

## Preview (vNext)

Sequence streaming of typed objects

Design principle: no token/delta event model. When a command returns a sequence (e.g., `list[T]`), Alloy yields whole, validated objects of type `T` as soon as they are complete.

```python
from dataclasses import dataclass
from alloy import command

@dataclass
class Person:
    name: str
    email: str

@command(output=list[Person], tools=[...])
def find_people(query: str) -> list[Person]: ...

for person in find_people.stream("kaggle meetup in LA"):
    print(person)

# Async variant
async for person in find_people.astream("kaggle meetup in LA"):
    print(person)
```

Semantics
- Supported outputs: `Sequence[T]` where `T` is a `dataclass` or `TypedDict` (strict mode applies).
- Yield contract: each item is a fully formed, schema‑validated `T`. No partial/delta objects.
- Ordering: preserves the model’s natural order.
- Tools: tool calls run inside the loop as usual; streaming pauses/resumes as needed.
- Errors: by default, validation errors raise and stop iteration.

Provider mapping: OpenAI/Anthropic/Gemini via streamed JSON array assembly; Ollama may fall back to non‑streaming for structured outputs.

Status: behind feature flag (`ALLOY_EXPERIMENTAL_STREAMING=1`). See Providers for support.
