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

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `ALLOY_MODEL` | str | `gpt-5-mini` | Model ID; determines provider (e.g., `gpt-5-mini`, `claude-…`, `gemini-…`, `ollama:<model>`) |
| `ALLOY_TEMPERATURE` | float | None | Sampling temperature; provider-specific handling |
| `ALLOY_MAX_TOKENS` | int | None | Cap on tokens for responses; some providers require this (Anthropic) |
| `ALLOY_DEFAULT_SYSTEM` | str | None | Default system prompt; alias: `ALLOY_SYSTEM` |
| `ALLOY_RETRY` | int | None | Retry count for transient failures |
| `ALLOY_MAX_TOOL_TURNS` | int | 10 | Max tool-call turn iterations in a single command run |
| `ALLOY_AUTO_FINALIZE_MISSING_OUTPUT` | bool | true | Issue one follow-up turn (no tools) to produce final structured output when missing |
| `ALLOY_EXTRA_JSON` | JSON object | `{}` | Provider-specific extras, merged into request (advanced) |

## Programmatic

```python
from alloy import configure

configure(model="gpt-5-mini", temperature=0.2)
```

## Provider Extras (advanced)

Pass provider knobs via `Config.extra` or `ALLOY_EXTRA_JSON`. Use generic keys first; provider‑prefixed fallbacks are supported for backward compatibility.

Primary keys
- `tool_choice`: str or dict
  - Examples: `"auto"`, `"any"`, `"none"`, or provider‑native dicts (e.g., Anthropic `{ "type": "auto" }`).
- `allowed_tools`: list[str]
  - Used by Gemini to restrict callable function names.
- `disable_parallel_tool_use`: bool
  - Used by Anthropic to prevent parallel tool execution.
- `ollama_api`: str
  - `"native"` or `"openai_chat"` — selects Ollama strategy.

Provider fallbacks (optional)
- OpenAI: `openai_tool_choice`
- Anthropic: `anthropic_tool_choice`, `anthropic_disable_parallel_tool_use`
- Gemini: `gemini_tool_choice`, `gemini_allowed_tools`
- Ollama (OpenAI‑chat shim): `ollama_tool_choice`

Examples
```bash
# Using ALLOY_EXTRA_JSON (shell)
export ALLOY_EXTRA_JSON='{
  "tool_choice": "auto",
  "disable_parallel_tool_use": true,
  "allowed_tools": ["get_weather", "get_time"],
  "ollama_api": "native"
}'
```

Keep the main API minimal; prefer defaults unless you need explicit control.
