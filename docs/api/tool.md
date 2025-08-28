# Tools

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

!!! note "See also"
    - Guide → Tools & Workflows: guide/tools-and-workflows.md
    - Guide → Contracts: guide/contracts.md

::: alloy.tool
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true
