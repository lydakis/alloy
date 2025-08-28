# Type System

How Python types map to provider schemas and back (~4 minutes).

---

- Inputs: Python annotations on tools/commands guide type checking and schema.
- Outputs: `output=T` → JSON Schema → provider structured output → Python `T`.
- Supported: primitives, dataclasses, lists of supported types; strict mode forbids open‑ended dicts.
- Errors: configuration errors for unsupported shapes; command errors for provider parse failures.

## Mapping Rules

- Primitives: providers require an object root; Alloy wraps primitives as `{ "value": <primitive> }` and unwraps on parse.
- Objects: dataclasses/TypedDicts become JSON Schema objects with `required` fields and `additionalProperties: false`.
- Arrays: supported when element type maps to a concrete schema.
- Unions/Optionals: not supported in strict mode.

## Example

```python
from dataclasses import dataclass
from alloy import command

@dataclass
class Person:
    name: str
    email: str

@command(output=Person)
def extract_person(text: str) -> str:
    return f"Extract name and email from: {text}"
```

Resulting schema (conceptual)

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "name": {"type": "string"},
    "email": {"type": "string"}
  },
  "required": ["name", "email"]
}
```

## Runtime Parsing

- Providers return the structured payload; Alloy validates against the schema and instantiates `T`.
- On parse failure, `CommandError` includes expected type and a snippet of the model output.
