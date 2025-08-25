# Enforcing Outputs

Alloy enforces outputs using provider Structured Outputs. A JSON Schema is sent to the model, and responses are parsed into your requested type.

## How it works (strict mode)

- Primitives (str, int, float, bool):
  - Providers require an object root. Alloy wraps primitives as `{ "value": <primitive> }` and unwraps `value` before parsing.
- Dataclasses (objects):
  - A JSON Schema is generated from the dataclass. All fields are required and `additionalProperties: false` is set.
- Arrays: `list[T]` is supported when `T` maps to a concrete schema as above.

There is no prompt shaping. Output shape is enforced only via Structured Outputs.

## Return Contracts

- Default `@command`: returns `str`. If the model produces no final output, Alloy raises `CommandError`.
- `@command(output=None)`: side-effect only. The wrapper always returns `None`.
- `@command(output=T)`: strict typed return. Returns `T` or raises on empty/mismatch.

Authoring guideline: the decorated function always returns a prompt `str`. The actual return type of the command is controlled by the decorator’s `output` parameter.

## Strict-mode limitations

Some types cannot produce a strict JSON Schema under provider constraints:

- Open-ended objects (`dict` or `dict[...]`) and `list[dict]` are not supported.
  - Strict mode requires `additionalProperties: false`. Accepting arbitrary keys would violate this, so Alloy raises a clear configuration error.
- Optional/Union types are not supported yet.

Use a concrete schema instead, such as a `@dataclass` or `TypedDict` with known fields.

Planned
- TypedDict outputs with strict schemas (equivalent to dataclasses).

## Errors and diagnostics

- If an unsupported output type is used in strict mode, Alloy raises `ConfigurationError` with guidance to use a concrete schema.
- If the model returns an unparsable payload or no final output, Alloy raises `CommandError` with the expected type and a snippet of the model output.

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

- OpenAI: Uses Responses `text={"format": {"type": "json_schema", ...}}` and unwraps primitives from `{"value": ...}`. When tool calls complete but no final structured output is present, Alloy may issue one follow-up turn (no tools) using the same schema to request the final answer. This is controlled by `auto_finalize_missing_output` (env `ALLOY_AUTO_FINALIZE_MISSING_OUTPUT`, default on). If still missing, the command raises.
- Anthropic/Gemini: Use their respective structured-output mechanisms with a JSON Schema.
- Some providers may require a final follow‑up turn to produce a structured response when tools are used. When `auto_finalize_missing_output` is enabled (default), Alloy performs a single follow‑up turn without tools to request the final structured answer.
- Ollama: No native structured outputs; strict mode not applied.
