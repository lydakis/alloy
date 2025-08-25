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

## Streaming with Tools

- Experimental. Alloy streams text and, where supported by providers, detects tool calls mid‑stream, executes tools locally, and continues streaming in a new pass. Structured outputs are not streamed.

## OpenAI specifics

- Uses the Responses API and loops with `previous_response_id` for tool calls.
- When a tool loop ends without a final structured output, Alloy issues one follow‑up turn (no tools) to finalize if `auto_finalize_missing_output` is enabled (default on). If still missing, the command raises.
- Temperature is omitted for models that don’t accept it (e.g., `gpt-5*`, `o1*`, `o3*`).
- Safety: cap tool iterations with `max_tool_turns` (configure or `ALLOY_MAX_TOOL_TURNS`).

## Gemini

- Supported via `google-genai`. Tools are supported in non‑streaming flows; streaming is text‑only (no tools in stream) in this scaffold.
- For strict typed outputs requested alongside tools, Alloy may issue a final follow‑up turn to produce a structured response when appropriate.
