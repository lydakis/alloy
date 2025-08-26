# Providers: Run Examples With Any Backend

Most examples work across OpenAI, Anthropic, Gemini, and Ollama with no code changes. Set `ALLOY_MODEL` and the provider API key, then run any script.

## Quickstart

- OpenAI
  - `export OPENAI_API_KEY=...`
  - `export ALLOY_MODEL=gpt-5-mini`
  - `python examples/10-commands/01_first_command.py`

- Anthropic (Claude)
  - `export ANTHROPIC_API_KEY=...`
  - `export ALLOY_MODEL=claude-sonnet-4-20250514`
  - Note: set `export ALLOY_MAX_TOKENS=512` (or your preferred limit) if required by the API
  - `python examples/10-commands/01_first_command.py`

- Google Gemini
  - `export GOOGLE_API_KEY=...`
  - `export ALLOY_MODEL=gemini-2.5-flash`
  - `python examples/10-commands/01_first_command.py`

- Ollama (local, optional)
  - Ensure the model is available: `ollama run <model>`
  - `export ALLOY_MODEL=ollama:<model>`
  - `python examples/10-commands/01_first_command.py`

## Notes
- Examples typically call `configure(temperature=0.2)` only. Provider/model is selected via `ALLOY_MODEL`.
- Tools and typed outputs are supported across providers; streaming is text-only.
- For integration tests, you can also set `ALLOY_IT_MODEL` to filter providers.
