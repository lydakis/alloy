# Ask

::: alloy.ask
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

```python
from alloy import ask, configure

configure(model="gpt-5-mini", temperature=0.2)

print(ask("Say hi in one word."))

for chunk in ask.stream("Write a one-liner about cats"):
    print(chunk, end="")
print()
```

!!! note "See also"
    - Guide → Core Concepts: guide/core-concepts.md
    - Guide → Streaming: guide/streaming.md
