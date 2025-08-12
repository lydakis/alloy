# Backends & Routing

Alloy auto-routes based on the `model` string:

- OpenAI: `gpt-*`, `gpt5*`, `openai*`
- Anthropic: `claude*`, `anthropic*`
- Gemini: `gemini*`, `google*` (uses `google-genai`)
- Ollama: `ollama:*` or `local:*`

Set `ALLOY_BACKEND=fake` to use a fake offline backend for examples.

Popular models (examples)
- OpenAI: `gpt-4o`, `gpt-4.1`, `gpt-5-mini`, `o3-mini`
- Anthropic: `claude-3.7-sonnet`, `claude-sonnet-4-20250514`, `claude-4-opus`, `claude-4.1-opus`
- Gemini: `gemini-2.5-pro`, `gemini-2.5-flash`
