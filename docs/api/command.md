# Command

::: alloy.command
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

Text command
```python
from alloy import command, configure

configure(model="gpt-5-mini", temperature=0.2)

@command  # returns str by default
def summarize(text: str) -> str:
    return f"Summarize in one sentence: {text}"

print(summarize("Alloy lets you write typed AI functions in Python."))
```

Typed output (dataclass)
```python
from dataclasses import dataclass
from alloy import command

@dataclass
class ArticleSummary:
    title: str
    key_points: list[str]

@command(output=ArticleSummary)
def summarize_article(text: str) -> str:
    return f"Summarize with: title and 3–5 key_points. Article: {text}"

res = summarize_article("Python emphasizes readability and has a vast ecosystem.")
print(res.title)
```

!!! note "See also"
    - Guide → Commands: guide/commands.md
    - Guide → Structured Outputs: guide/structured-outputs.md
    - Guide → Tools & Workflows: guide/tools-and-workflows.md
    - Guide → Streaming: guide/streaming.md
