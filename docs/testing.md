# Testing

Run unit, integration, and parity-live tests locally. Scenarios now run across all available providers by default.

---

## Quick start

- Unit tests
  - `pytest -q`
- Lint/type
  - `ruff check .` and `mypy .`

---

## Providers and credentials

- OpenAI: set `OPENAI_API_KEY`
- Anthropic: set `ANTHROPIC_API_KEY`
- Google Gemini: set `GOOGLE_API_KEY`
- Ollama: install the SDK and ensure the server is running (`ollama list` must succeed)

If only some providers are configured, tests parameterized across providers will run for those and skip others.

---

## Integration: Providers (e2e)

- Location: `tests/integration/providers/`
- Run: `pytest -q tests/integration/providers`
- Each provider suite expects its corresponding credentials or Ollama server.
- Ollama API strategy
  - Default is native (`/api/chat`). To use the OpenAI-compatible Chat Completions path, set `extra={"ollama_api": "openai_chat"}` in `configure(...)` or `ALLOY_EXTRA_JSON`.
  - Config auto-routes models of the form `"ollama:*gpt-oss*"` to `openai_chat` unless explicitly overridden.

---

## Integration: Scenarios (cross-provider)

- Location: `tests/integration/scenarios/`
- Run: `pytest -q tests/integration/scenarios`
- Always parameterized across all available providers:
  - OpenAI, Anthropic, Gemini (when API keys are present)
  - Ollama (when SDK installed and server running)
- Default model per provider can be tuned with environment variables:
  - `ALLOY_SCENARIOS_OPENAI_MODEL` (default: `gpt-5-mini`)
  - `ALLOY_SCENARIOS_ANTHROPIC_MODEL` (default: `claude-sonnet-4-20250514`)
  - `ALLOY_SCENARIOS_GEMINI_MODEL` (default: `gemini-2.5-flash`)
  - `ALLOY_OLLAMA_SCENARIO_MODEL` (default: `ollama:llama3.2`)

---

## Parity-live

- Location: `tests/parity_live/`
- Run: `pytest -m parity_live -q`
- Includes OpenAI, Anthropic, Gemini, and Ollama by default.
  - Ollama requires the SDK and a running server. Default model can be overridden with `ALLOY_OLLAMA_PARITY_MODEL`.
  - The Ollama provider defaults to native; set `ALLOY_OLLAMA_API=openai_chat` to force the compat path.

---

## Notes

- Streaming is text-only for all providers; commands that use tools or non-string outputs do not stream.
- Scenarios choose a single fallback model if no providers are available.
- Config auto-routing: `get_config()` sets `extra["ollama_api"]="openai_chat"` for models matching `"ollama:*gpt-oss*"`, unless explicitly set.
