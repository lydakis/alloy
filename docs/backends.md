# Backends & Routing

Alloy auto-routes based on the `model` string:

- OpenAI: `gpt-*`, `gpt5*`, `openai*`
- Anthropic: `claude*`, `anthropic*`
- Gemini: `gemini*`, `google*` (uses `google-genai`)
- Ollama: `ollama:*` or `local:*`

Set `ALLOY_BACKEND=fake` to use a fake offline backend for examples.
