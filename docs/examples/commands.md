# Commands

Create reusable text and typed commands (4–6 minutes).

---

## Example

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

Expected: a structured object with `title` and 3–5 `key_points`.

## Links (GitHub)
- [First command](https://github.com/lydakis/alloy/blob/main/examples/10-commands/01_first_command.py)
- [Async command](https://github.com/lydakis/alloy/blob/main/examples/10-commands/03_async_command.py)
- [Typed dataclass output](https://github.com/lydakis/alloy/blob/main/examples/20-typed/02_dataclass_output.py)
- [List of typed items](https://github.com/lydakis/alloy/blob/main/examples/20-typed/03_list_output.py)
- Folders: [10-commands](https://github.com/lydakis/alloy/tree/main/examples/10-commands) · [20-typed](https://github.com/lydakis/alloy/tree/main/examples/20-typed)

Streaming: see Guide → Streaming (text‑only today).
