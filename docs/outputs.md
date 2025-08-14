# Enforcing Outputs

Alloy helps ensure your model returns the right shape using two layers:

- Provider structured outputs (preferred): When supported, Alloy passes a JSON Schema to the provider and unwraps primitives automatically.
- Prompt shaping (fallback): Alloy appends minimal guardrails to steer models toward strictly formatted outputs, and raises a clear error if parsing fails.

## How it works

- Primitives (float/int/bool/str):
  - OpenAI / Anthropic / Gemini: Alloy wraps primitives as `{ "value": <primitive> }` (providers require an object) and requests structured output. The backend unwraps `value` before parsing.
  - Others (e.g., Ollama): Alloy adds a short instruction asking for a single JSON object like `{ "value": 49.99 }`. Parsing then extracts `value` and coerces to the requested type.

- Objects / dataclasses:
  - Alloy derives a JSON Schema from your dataclass and requests the provider produce JSON that matches it. As a fallback, Alloy adds a short prompt instruction to output JSON that matches the schema exactly.

## Error handling

If the model returns something that cannot be parsed, Alloy raises a `CommandError` describing the expected type and shows a short snippet of the model output to aid debugging.

Example error:

```
CommandError: Failed to parse model output as float: 'Please provide the text…'
```

## Example

```python
from alloy import command

@command(output=float)
def extract_price(text: str) -> str:
    """Extract price from text."""
    return f"Extract the price (number only) from: {text}"

print(extract_price("This item costs $49.99."))  # -> 49.99
```

This will request structured output where available; otherwise the appended hint instructs the model to return only the number (or a JSON object `{ "value": 49.99 }` for providers like Ollama).

## Provider notes

- OpenAI: Uses `response_format={"type": "json_schema"}` and unwraps primitives from `{ "value": ... }`.
- Anthropic: Uses `response_format` with JSON Schema; primitives are wrapped and unwrapped similarly.
- Gemini: Uses `generation_config.response_schema` and `response_mime_type=application/json`, with primitive unwrapping.
- Ollama: No native structured outputs yet; Alloy enforces via prompt instructions and tolerant parsing.
