# alloy (top-level package)

## Usage

```python
from alloy import ask, command, tool, configure

configure(model="gpt-5-mini", temperature=0.2)

@command
def summarize(text: str) -> str:
    return f"Summarize in one sentence: {text}"

print(ask("Say hi succinctly."))
print(summarize("Alloy lets you write typed AI functions in Python."))
```

!!! note "See also"
    - Guide → Core Concepts: guide/core-concepts.md
    - API → Ask: api/ask.md
    - API → Command: api/command.md
    - API → Tools: api/tool.md

::: alloy
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true
