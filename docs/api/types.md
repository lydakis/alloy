# Types

::: alloy.types
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

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

print(extract_person("Ada, ada@example.com"))
```

TypedDict outputs
```python
from typing import TypedDict
from alloy import command

class Product(TypedDict):
    name: str
    price: float

@command(output=Product)
def make() -> str:
    return "Return a Product with name='Test' and price=9.99 (numeric literal)."

out = make()
assert isinstance(out, dict)
```

Validation errors
```python
from alloy import CommandError

try:
    extract_person("Incomplete data")  # may raise if schema cannot be satisfied
except CommandError as e:
    print("Parse failed:", e)
```

!!! note "See also"
    - Guide → Structured Outputs: guide/structured-outputs.md
