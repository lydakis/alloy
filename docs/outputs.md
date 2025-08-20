# Enforcing Outputs

Alloy enforces outputs using provider Structured Outputs. A JSON Schema is sent to the model, and responses are parsed into your requested type.

## How it works (strict mode)

- Primitives (str, int, float, bool):
  - Providers require an object root. Alloy wraps primitives as `{ "value": <primitive> }` and unwraps `value` before parsing.
- Dataclasses (objects):
  - A JSON Schema is generated from the dataclass. All fields are required and `additionalProperties: false` is set.
- Arrays: `list[T]` is supported when `T` maps to a concrete schema as above.

There is no prompt shaping. Output shape is enforced only via Structured Outputs.

## Strict-mode limitations

Some types cannot produce a strict JSON Schema under provider constraints:

- Open-ended objects (`dict` or `dict[...]`) and `list[dict]` are not supported.
  - Strict mode requires `additionalProperties: false`. Accepting arbitrary keys would violate this, so Alloy raises a clear configuration error.
- Optional/Union types are not supported yet.

Use a concrete schema instead, such as a `@dataclass` or `TypedDict` with known fields.

## Errors and diagnostics

- If an unsupported output type is used in strict mode, Alloy raises `ConfigurationError` with guidance to use a concrete schema.
- If the model returns an unparsable payload, Alloy raises `CommandError` that includes the expected type and a snippet of the model output.

Example parse error:

```
CommandError: Failed to parse model output as float: 'Please provide the text…'
```

## Example

```python
from alloy import command

@command(output=float)
def extract_price(text: str) -> str:
    return f"Extract the price (number only) from: {text}"

print(extract_price("This item costs $49.99."))  # -> 49.99
```

## Provider notes

- OpenAI: Uses Responses `text={"format": {"type": "json_schema", ...}}` and unwraps primitives from `{"value": ...}`.
- Anthropic/Gemini: Use their respective structured-output mechanisms with a JSON Schema.
- Ollama: No native structured outputs; strict mode not applied.
