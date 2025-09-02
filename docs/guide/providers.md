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
# Anthropic requires max_tokens; Alloy uses 2048 if unset
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
| Anthropic (Claude) | Yes | Yes | Yes | Yes | No | No | Requires `max_tokens` (Alloy uses 2048 if unset). |
| Google Gemini | Yes | Yes | Yes | Yes | No | No | Requires `max_tool_turns` configured; uses `google-genai`. |
| Ollama (local) | Yes | Yes | Yes | Yes | No | No | Two APIs: native `/api/chat` (JSON Schema via `format`, full Ollama options) and OpenAI‑compatible Chat Completions. Default is native; config auto‑routes `ollama:*gpt-oss*` to compat unless overridden via `extra["ollama_api"]`. |
| Fake (offline) | Yes | No | Yes (deterministic stub) | Yes | No | No | Offline backend for CI/examples; not for production. |

Note: “Streaming + Structured” means sequence‑of‑objects only (e.g., `list[T]`); Alloy does not stream partial object deltas.

### Ollama specifics

- API selection: `extra["ollama_api"] = "native" | "openai_chat"`. Default: `native`; config auto‑routes `ollama:*gpt-oss*` to `openai_chat` unless explicitly set.
- Native API advantages: strict structured outputs with `format={JSON Schema}`, Ollama‑specific options (e.g., `num_predict`, `num_ctx`).
- OpenAI‑compat advantages: drop‑in with OpenAI clients (e.g., gpt‑oss). Some Ollama knobs are not exposed here.
- Limitations: streaming is text‑only (no tools or structured outputs while streaming). Tool calling requires a tool‑capable model.

---

## Migration notes

- Model naming may change; prefer lightweight defaults (e.g., `gpt-5-mini`, `gemini-2.5-flash`).
- Tool result shapes and limits vary; Alloy normalizes common cases and raises clear errors where not supported.
- See Guide → Streaming for exact streaming semantics and preview status.
