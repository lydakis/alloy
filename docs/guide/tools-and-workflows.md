# Tools & Workflows

Add local capabilities and assemble small workflows in ~6 minutes. Requires Python 3.10+ and `pip install alloy-ai`.

---

## Tool contract

- Plain Python function decorated with `@tool`.
- Type annotations describe inputs/outputs. Add contracts (`@require/@ensure`) for invariants.

Tip: Use Design by Contract (DbC) to keep steps safe and explicit — see [Guide → Contracts](contracts.md) (background: [Design by Contract](https://en.wikipedia.org/wiki/Design_by_contract)).

```python
from alloy import tool, require, ensure

@tool
@require(lambda ba: isinstance(ba.arguments.get("path"), str), "path must be a string")
@ensure(lambda out: isinstance(out, str) and len(out) < 10_000, "output too large")
def read_text(path: str) -> str:
    return open(path, "r", encoding="utf-8", errors="ignore").read()
```

## Attach tools to a command

```python
from alloy import command

@command(output=str, tools=[read_text])
def analyze_file(path: str) -> str:
    return f"Read the file, then list 3 key insights. path={path}"
```

Tip
- Parameters with default values are optional for tools. Only parameters without defaults are required by the model. This applies to nested dataclasses used as tool parameters as well.

## Multi‑step workflows

- Compose Python functions; no special orchestration layer needed.
- Keep steps small and verifiable; use contracts and typed outputs between steps.

Patterns
- Validate → enrich → save (DBC guards order and effects)
- Fetch → parse → extract (typed outputs ensure shape at each step)
- Fan‑out tools (parallel where provider supports it), then reduce

See also: Tool Recipes for copy‑pasteable helpers (HTTP fetch, local file search, etc.).
