# Alloy Examples

Minimal, practical snippets that demonstrate Alloy’s core philosophy:
Python for logic. English for intelligence.

## Setup
- Install package (editable suggested): `pip install -e '.[dev]'`
- Load environment: `cp .env.example .env` (if available) and set `OPENAI_API_KEY`
- Optional: run offline with a fake backend: `export ALLOY_BACKEND=fake`

## Running
- Each example is a standalone script: `python examples/<category>/<file>.py`
- Default model is `gpt-5-mini`; you can override with `configure(...)` or `ALLOY_MODEL`.
- Streaming policy: Commands → Streaming constraints: https://docs.alloy.fyi/commands/#sync-async-and-streaming

## Provider Setup (quick)

Set one of the following before running examples. Full configuration knobs: https://docs.alloy.fyi/configuration/

- OpenAI
  - `export OPENAI_API_KEY=...`
  - `export ALLOY_MODEL=gpt-5-mini`
- Anthropic (Claude)
  - `export ANTHROPIC_API_KEY=...`
  - `export ALLOY_MODEL=claude-sonnet-4-20250514`
  - If required: `export ALLOY_MAX_TOKENS=512`
- Google Gemini
  - `export GOOGLE_API_KEY=...`
  - `export ALLOY_MODEL=gemini-2.5-flash`
- Ollama (local)
  - Ensure a model is running: `ollama run <model>`
  - `export ALLOY_MODEL=ollama:<model>`

## Structure (progressive path)
- `00-explore/` — Explore with `ask()` (no structure needed)
- `10-commands/` — First commands, sync and async
- `20-typed/` — Provider-enforced typed outputs (primitives, dataclasses, lists)
- `30-tools/` — `@tool` basics, tools with commands, parallel calls, recipes (HTTP/file/SQL)
- `40-contracts/` — Design by Contract (`@require/@ensure`) and workflows
- `50-composition/` — Compose commands (routing, recursive analysis, translator network)
- `60-integration/` — Pandas, Flask endpoint, batch processing, pytest generator
- `70-providers/` — Same task across OpenAI / Anthropic / Gemini / Ollama + setup
- `80-patterns/` — RAG, self-refine, PII guardrail, streaming, retry, memory, conversation history
- `90-advanced/` — Deep-agents (dynamic + minimal), OCR via tool, observability, evals

## Offline Mode
- For quick demos without provider keys: `ALLOY_BACKEND=fake` will return deterministic canned responses for typed outputs.

## Providers
- Set the provider API key and `ALLOY_MODEL`:
  - OpenAI: `export OPENAI_API_KEY=...; export ALLOY_MODEL=gpt-5-mini`
  - Anthropic (Claude): `export ANTHROPIC_API_KEY=...; export ALLOY_MODEL=claude-sonnet-4-20250514`
    - If required by the API, also set: `export ALLOY_MAX_TOKENS=512`
  - Google Gemini: `export GOOGLE_API_KEY=...; export ALLOY_MODEL=gemini-2.5-flash`
  - Ollama (local, optional): `export ALLOY_MODEL=ollama:<model>` (ensure the model is running via `ollama run <model>`)
- Most examples only set `temperature=0.2`. The model is read from `ALLOY_MODEL` so examples run across providers without code changes.

## Notes
- Examples aim for 50–150 lines each, minimal dependencies, and deterministic behavior (e.g., `temperature=0.2`).
- Use `from alloy import ...` for all imports (no submodules).

## Navigation Tips
- Provider: set `ALLOY_MODEL` and the relevant API key (see 70-providers/README.md).
- Tool loops: default `max_tool_turns=10` (override via env or `configure`).
