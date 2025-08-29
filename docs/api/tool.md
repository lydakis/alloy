# Tools

::: alloy.tool
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

```python
from alloy import command, tool

@tool
def word_count(text: str) -> int:
    return len(text.split())

@command(tools=[word_count])
def analyze(text: str) -> str:
    return f"Use word_count(text), then suggest one clarity improvement.\\nText: {text}"

print(analyze("Alloy makes typed AI functions feel like normal Python."))
```

Contracts (Design by Contract)
```python
from alloy import tool, require, ensure

@tool
@require(lambda ba: ba.arguments.get("x", 0) >= 0, "x must be non-negative")
@ensure(lambda r: r >= 0, "result must be non-negative")
def sqrt_floor(x: int) -> int:
    import math
    return int(math.sqrt(x))
```

### Optional parameters

- Tool parameters with default values are optional. Only parameters without defaults are included in the JSON Schema `required` list.
- Nested dataclasses in tool parameters also respect defaults (their fields with defaults are not required).
- Applies across OpenAI, Anthropic, and Gemini; unknown top‑level keys are rejected (`additionalProperties: false`).

!!! note "See also"
    - Guide → Tools & Workflows: guide/tools-and-workflows.md
    - Guide → Contracts: guide/contracts.md
