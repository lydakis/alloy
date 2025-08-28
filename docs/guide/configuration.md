# Configuration

Audience: developers configuring models, retries, and runtime knobs.
Outcome: apply env, global, and per‑call configuration with clear precedence.
Time: 4 minutes
Prereqs: Python 3.10+, `pip install alloy-ai`.

---

## Precedence

1. Per‑call overrides (e.g., `ask(..., model=...)`)
2. `configure(...)` and context scopes
3. Environment variables (`ALLOY_*`)
4. Built‑in defaults (`model="gpt-5-mini"`, `max_tool_turns=10`)

## Environment variables

- `ALLOY_MODEL`
- `ALLOY_TEMPERATURE`
- `ALLOY_MAX_TOKENS`
- `ALLOY_SYSTEM` or `ALLOY_DEFAULT_SYSTEM`
- `ALLOY_RETRY`
- `ALLOY_MAX_TOOL_TURNS`
- `ALLOY_EXTRA_JSON` (provider‑specific)

## Programmatic

```python
from alloy import configure

configure(model="gpt-5-mini", temperature=0.2)
```
