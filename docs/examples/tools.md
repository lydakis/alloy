# Tools

Expose local capabilities and apply contracts (5–8 minutes).

---

## Example

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

Expected: a short analysis referencing the word count.

## Links (GitHub)
- [Simple tool](https://github.com/lydakis/alloy/blob/main/examples/30-tools/01_simple_tool.py)
- [Parallel tool calls](https://github.com/lydakis/alloy/blob/main/examples/30-tools/03_parallel_tools.py)
- [Tool recipes](https://github.com/lydakis/alloy/blob/main/examples/30-tools/04_tool_recipes.py)
- [Contracts workflow](https://github.com/lydakis/alloy/blob/main/examples/40-contracts/02_workflow_contracts.py)
- Folders: [30-tools](https://github.com/lydakis/alloy/tree/main/examples/30-tools) · [40-contracts](https://github.com/lydakis/alloy/tree/main/examples/40-contracts)

Safety: prefer small, idempotent tools with clear messages in `@require/@ensure`.

See also: Guide → Contracts (guide/contracts.md) and [Design by Contract](https://en.wikipedia.org/wiki/Design_by_contract).
