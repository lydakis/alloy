# Streaming

Streaming behavior is stable for text and currently available with tool-calling on backends that support it. Typed/structured streaming is not implemented yet. Requires Python 3.10+ and `pip install alloy-ai`.

---

## Current (stable)

- Text streaming.
- Tools can stream when the configured backend advertises support (OpenAI Responses, Anthropic Claude, and Google Gemini today).

> Warning: Structured outputs are not supported while streaming. Non-string result types must be retrieved via non-streaming calls.

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

## Future (planned)

Sequence streaming of typed objects is planned but not yet implemented. When added, each yielded chunk will be a full validated object.
