# Configuration

Alloy reads configuration from, in precedence order:

1. Per-call overrides (e.g., `ask(..., model=...)`)
2. `configure(...)` and context scopes
3. Environment variables (`ALLOY_*`)
4. Built-in defaults (`model="gpt-5-mini"`, `max_tool_turns=2`)

## Environment variables

- `ALLOY_MODEL`
- `ALLOY_TEMPERATURE`
- `ALLOY_MAX_TOKENS`
- `ALLOY_SYSTEM` or `ALLOY_DEFAULT_SYSTEM`
- `ALLOY_RETRY`
- `ALLOY_MAX_TOOL_TURNS`
- `ALLOY_EXTRA_JSON` (provider-specific)

## Programmatic

```python
from alloy import configure

configure(model="gpt-5-mini", temperature=0.2)
```

