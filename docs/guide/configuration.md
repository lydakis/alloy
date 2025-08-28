# Configuration

Configure models, retries, and runtime knobs in ~4 minutes. Requires Python 3.10+ and `pip install alloy-ai`.

---

## Quick Start

```bash
export OPENAI_API_KEY=...
export ALLOY_MODEL=gpt-5-mini
```

## Precedence

1. Per‑call overrides (e.g., `ask(..., model=...)`)
2. `configure(...)` and context scopes
3. Environment variables (`ALLOY_*`)
4. Built‑in defaults (`model="gpt-5-mini"`, `max_tool_turns=10`)

## All Settings (env)

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
