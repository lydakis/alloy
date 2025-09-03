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

Pass provider knobs via `Config.extra` or `ALLOY_EXTRA_JSON`. Use provider‑prefixed keys (one way), reflecting provider differences.

Provider keys

| Provider | Key | Type | Example | Notes |
|----------|-----|------|---------|-------|
| OpenAI | `openai_tool_choice` | str or dict | `"auto"`, `"required"`, or function spec dict | Overrides default tool choice when tools are present |
| Anthropic | `anthropic_tool_choice` | dict | `{ "type": "auto" | "any" | "tool" | "none" }` | Matches Anthropic tool choice semantics |
| Anthropic | `anthropic_disable_parallel_tool_use` | bool | `true` | Disables parallel tool use (when applicable) |
| Gemini | `gemini_tool_choice` | str or dict | `"AUTO"`, `"ANY"`, `"NONE"` | Tool calling mode |
| Gemini | `gemini_allowed_tools` | list[str] | `["f1", "f2"]` | Restrict callable function names |
| Ollama | `ollama_api` | str | `"native"` or `"openai_chat"` | Select API strategy; native uses `/api/chat` with `format={JSON Schema}` |
| Ollama (OpenAI‑chat) | `ollama_tool_choice` | str or dict | `"auto"`, `"required"`, or function spec dict | OpenAI‑compatible tool choice when using `openai_chat` |

Examples
```bash
# Using ALLOY_EXTRA_JSON (shell)
export ALLOY_EXTRA_JSON='{
  "openai_tool_choice": "auto",
  "anthropic_tool_choice": {"type":"auto"},
  "anthropic_disable_parallel_tool_use": true,
  "gemini_tool_choice": "AUTO",
  "gemini_allowed_tools": ["get_weather", "get_time"],
  "ollama_api": "native"
}'
```

Keep the main API minimal; prefer defaults unless you need explicit control.
