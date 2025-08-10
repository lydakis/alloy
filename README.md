Alloy (Python): Python for logic. English for intelligence.

License: MIT

This repository contains an early scaffold of the Alloy library per `alloy-spec-v1.md`.

Quick start
- Install: `pip install openai python-dotenv`
- Create `.env` with `OPENAI_API_KEY=...`
- Use the API:

```python
from dataclasses import dataclass
from dotenv import load_dotenv
from alloy import command, ask, configure

load_dotenv()
# Optional: configure() — default model is `gpt-5-mini` if omitted
# configure(model="gpt-5-mini", temperature=0.7)

@command(output=float)
def ExtractPrice(text: str) -> str:
    """Extract price from text."""
    return f"Extract the price (number only) from: {text}"

print(ExtractPrice("This item costs $49.99."))
print(ask("Say hi"))
```

Notes
- OpenAI backend is implemented for sync/async/streaming.
- Streaming with tools is not yet supported.
- For structured outputs, Alloy attempts to use OpenAI structured responses (JSON schema). If unavailable, the model may still return JSON, which Alloy parses best-effort.
- Configuration defaults: Alloy uses `model=gpt-5-mini` if `configure(...)` is not called. You can also set process environment variables instead of a `.env` file:
  - `ALLOY_MODEL`, `ALLOY_TEMPERATURE`, `ALLOY_MAX_TOKENS`, `ALLOY_SYSTEM`/`ALLOY_DEFAULT_SYSTEM`, `ALLOY_RETRY`.
  - Example: `export ALLOY_MODEL=gpt-4o` then run your script.

Examples
- See `examples/basic_usage.py` and `examples/tools_demo.py` (tools + contracts).

Offline mode (dev only)
- To run examples without network/API keys, set `ALLOY_BACKEND=fake`.
- Example: `ALLOY_BACKEND=fake python examples/basic_usage.py`

Config precedence
- Defaults: `model=gpt-5-mini`, `max_tool_turns=2`.
- Process env (ALLOY_*) overrides defaults.
- Context/use_config and `configure(...)` override env/defaults.
- Per-call overrides (e.g., `ask(..., model=...)`) override everything above.

Make targets
- `make setup` — install dev deps and package in editable mode.
- `make test`, `make lint`, `make typecheck` — CI-like checks.
- `make examples` — runs `examples/basic_usage.py` and `examples/tools_demo.py`.
  - Tip: `ALLOY_BACKEND=fake make examples` to run offline.

Troubleshooting
- API key: Ensure `OPENAI_API_KEY` is set (process env or `.env`).
- Model choice: Prefer `gpt-5-mini` for fastest latency; switch via `configure(model=...)` or `ALLOY_MODEL`.
- Timeouts/slow runs: Reduce `max_tokens`, lower `temperature`, prefer smaller models, and cap tool loops.
- Tool loops: Alloy caps tool iterations by default (`max_tool_turns=2`). Adjust via `configure(max_tool_turns=1)` or env `ALLOY_MAX_TOOL_TURNS`.
- Rate limits (429): Shorten prompts/outputs, add retries with backoff, or use lower-throughput settings.

Integration tests
- OpenAI: Set `OPENAI_API_KEY` (and optionally `ALLOY_IT_MODEL`, default `gpt-5-mini`). Run `pytest -q` — OpenAI integration tests auto-enable.
- Anthropic: Set `ANTHROPIC_API_KEY` and `ALLOY_IT_MODEL=claude-3.5-sonnet` (or another Claude). Run `pytest -q` — Anthropic integration tests auto-enable.
- Gemini: Set `GOOGLE_API_KEY` and `ALLOY_IT_MODEL=gemini-1.5-pro` (or another Gemini). Run `pytest -q` — Gemini integration tests auto-enable.
  - SDK note: The default extra now uses `google-genai` (GA). If you need the older SDK, install the legacy extra.

How to run locally
- `pip install openai python-dotenv`
- Create `.env` with `OPENAI_API_KEY=...`
- Option A (no install):
  - `python examples/basic_usage.py`
  - `python examples/tools_demo.py`
  - (examples add `src/` to `sys.path` for you)
- Option B (editable install):
  - `pip install -e .`
  - Then run from anywhere.

.env example
```
OPENAI_API_KEY=sk-...
```
Support matrix (v1)
- OpenAI (GPT-4/5 and o-series): completions, typed commands, ask, streaming (no tools in stream), tool-calling, structured JSON for object schemas, tool-loop cap.
- Anthropic (Claude 3/3.5): completions and tool-calling loop (no streaming yet).
- Google (Gemini 1.5): basic completions (no tools/streaming in scaffold). Uses `google-genai` by default; `google-generativeai` supported via legacy extra.
- Ollama (local): basic completions via `model="ollama:<name>"` (no tools/streaming in scaffold).
- ReAct fallback: not implemented yet (planned for local models/LLMs without native tools).

Install options
- Base: `pip install alloy` (includes OpenAI + python-dotenv).
- All providers: `pip install 'alloy[providers]'` (OpenAI, Anthropic, Gemini via `google-genai`, Ollama).
- Specific extras: `pip install 'alloy[anthropic]'`, `pip install 'alloy[gemini]'`, `pip install 'alloy[gemini-legacy]'`, `pip install 'alloy[ollama]'`.
