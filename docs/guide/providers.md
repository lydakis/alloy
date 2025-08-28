# Providers

Set up OpenAI/Anthropic/Gemini/Ollama quickly and consult a single capability matrix. Requires Python 3.10+ and `pip install alloy-ai`.

---

## Setup (quick)

Pick a provider, set its API key, and choose a model ID via `ALLOY_MODEL`. No code changes required.

OpenAI
```bash
export OPENAI_API_KEY=sk-...
export ALLOY_MODEL=gpt-5-mini
```

Anthropic (Claude)
```bash
export ANTHROPIC_API_KEY=...
export ALLOY_MODEL=claude-sonnet-4-20250514
# Anthropic requires max_tokens; Alloy uses 512 if unset
```

Google Gemini
```bash
export GOOGLE_API_KEY=...
export ALLOY_MODEL=gemini-2.5-flash
```

Ollama (local)
```bash
export ALLOY_MODEL=ollama:<model>
```

Fake (offline/demo)
```bash
export ALLOY_BACKEND=fake
```

---

## Capability Matrix (canonical)

| Provider | Text | Tools | Structured Outputs | Streaming Text | Streaming + Tools | Streaming + Structured | Notes |
|---|---|---|---|---|---|---|---|
| OpenAI | Yes | Yes | Yes | Yes | No | No | Uses Responses API; auto-finalize missing structured output on OpenAI when enabled. |
| Anthropic (Claude) | Yes | Yes | Yes | Yes | No | No | Requires `max_tokens` (Alloy uses 512 if unset). |
| Google Gemini | Yes | Yes | Yes | Yes | No | No | Requires `max_tool_turns` configured; uses `google-genai`. |
| Ollama (local) | Yes | No | Limited | No | No | No | No native structured outputs; primitives best-effort via JSON prompt; streaming and tools not implemented in scaffold. |
| Fake (offline) | Yes | No | Yes (deterministic stub) | Yes | No | No | Offline backend for CI/examples; not for production. |

Note: “Streaming + Structured” means sequence‑of‑objects only (e.g., `list[T]`); Alloy does not stream partial object deltas.

---

## Migration notes

- Model naming may change; prefer lightweight defaults (e.g., `gpt-5-mini`, `gemini-2.5-flash`).
- Tool result shapes and limits vary; Alloy normalizes common cases and raises clear errors where not supported.
- See Guide → Streaming for exact streaming semantics and preview status.
