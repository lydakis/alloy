# Errors

::: alloy.errors
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

```python
from alloy import command, CommandError

@command(output=int)
def compute() -> str:
    return "Return 6*7 as a number."

try:
    print(compute())
except CommandError as e:
    print("Model error:", e)
```

!!! note "See also"
    - Guide → Production: guide/production.md
