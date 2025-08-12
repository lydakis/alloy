# Alloy (Python)

Python for logic. English for intelligence.

Alloy helps you integrate intelligence into deterministic programs with typed Python functions.
Declare a function with `@command(output=...)`, and Alloy routes to an LLM provider, enforces
structured outputs, and returns typed results you can depend on.

[![CI](https://github.com/lydakis/alloy/actions/workflows/ci.yml/badge.svg)](https://github.com/lydakis/alloy/actions/workflows/ci.yml)
[![Docs](https://github.com/lydakis/alloy/actions/workflows/docs.yml/badge.svg)](https://lydakis.github.io/alloy/)
[![Docs Site](https://img.shields.io/badge/docs-website-blue)](https://lydakis.github.io/alloy/)
[![PyPI](https://img.shields.io/pypi/v/alloy-ai.svg)](https://pypi.org/project/alloy-ai/)
[![Python Versions](https://img.shields.io/pypi/pyversions/alloy-ai.svg)](https://pypi.org/project/alloy-ai/)
[![Downloads](https://pepy.tech/badge/alloy-ai)](https://pepy.tech/project/alloy-ai)
[![Coverage](https://codecov.io/gh/lydakis/alloy/branch/main/graph/badge.svg)](https://codecov.io/gh/lydakis/alloy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

License: MIT

This repository contains an early scaffold of the Alloy library per `alloy-spec-v1.md`.

### Example: CSV to API

```python
from alloy import command
import pandas as pd

@command(output=list[dict])
def CSVToAPI(df: pd.DataFrame, endpoint_example: str) -> str:
    """Intelligently map CSV columns to API format."""
    return f"Map this data {df.head()} to match API: {endpoint_example}"

df = pd.read_csv("messy_customer_data.csv")
api_calls = CSVToAPI(df, "POST /customers {fullName, emailAddress, subscriptionTier}")
for payload in api_calls:
    requests.post("https://api.your-saas.com/customers", json=payload)
```

This example maps rows from a DataFrame into request payloads for an API, returning a typed `list[dict]` you can post.

Quick start
- Install (all providers): `pip install 'alloy-ai[providers]'`
- Or minimal (OpenAI only): `pip install alloy-ai`
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

Enforcing outputs
- Alloy biases models to return the expected shape and uses provider structured outputs where available. If parsing still fails, you get a clear error.
- Docs: https://lydakis.github.io/alloy/outputs/

Notes
- OpenAI backend is implemented for sync/async/streaming.
- Streaming with tools is not yet supported.
- Structured outputs: Alloy uses provider JSON Schema features (OpenAI/Anthropic/Gemini) and prompt guardrails. See Enforcing outputs above.
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
- Anthropic: Set `ANTHROPIC_API_KEY` and `ALLOY_IT_MODEL=claude-sonnet-4-20250514` (or another Claude like `claude-3.7-sonnet`). Run `pytest -q` — Anthropic integration tests auto-enable.
- Gemini: Set `GOOGLE_API_KEY` and `ALLOY_IT_MODEL=gemini-2.5-pro` (or `gemini-2.5-flash`). Run `pytest -q` — Gemini integration tests auto-enable.
  - SDK note: Gemini support uses `google-genai` (GA).

How to run locally
- Install providers bundle: `pip install 'alloy-ai[providers]'`
- Create `.env` with `OPENAI_API_KEY=...`
- Option A (no install):
  - `python examples/basic_usage.py`
  - `python examples/tools_demo.py`
  - (examples add `src/` to `sys.path` for you)
- Option B (editable install):
  - `pip install -e '.[providers]'`
  - Then run from anywhere.

.env example
```
OPENAI_API_KEY=sk-...
```
Support matrix (v1)
- OpenAI (GPT-4/5 and o-series): completions, typed commands, ask, streaming (no tools in stream), tool-calling, structured JSON for object schemas, tool-loop cap.
- Anthropic (Claude 3.7 / Sonnet 4 / Opus 4/4.1): completions and tool-calling loop (no streaming yet).
- Google (Gemini 2.5 Pro/Flash): basic completions (no tools/streaming in scaffold). Uses `google-genai` by default.
- Ollama (local): basic completions via `model="ollama:<name>"` (no tools/streaming in scaffold).
- ReAct fallback: not implemented yet (planned for local models/LLMs without native tools).

Install options
- Base: `pip install alloy-ai` (includes OpenAI + python-dotenv).
- All providers: `pip install 'alloy-ai[providers]'` (OpenAI, Anthropic, Gemini via `google-genai`, Ollama).
- Specific extras: `pip install 'alloy-ai[anthropic]'`, `pip install 'alloy-ai[gemini]'`, `pip install 'alloy-ai[ollama]'`.
Documentation
- Full docs: https://lydakis.github.io/alloy/

Why Alloy vs X

- Raw SDKs: Minimal glue, limited structure handling. Alloy provides typed outputs, provider routing, and a simple tool loop.
- LangChain: Rich orchestration features and chains. Alloy stays minimal: Python functions that return typed results without introducing a new framework.
- Instructor/Pydantic: Strong for OpenAI JSON typing. Alloy generalizes the idea across providers (OpenAI, Anthropic, Gemini), adds tools/retry/routing, and degrades gracefully when structure is not enforced.
- DSPy/Program synthesis: Optimizes pipelines and prompts. Alloy focuses on straightforward, production‑oriented building blocks: short prompts, typed outputs, and predictable defaults.
- Guidance/templating: Emphasizes prompt templates. Alloy emphasizes typed commands and provider structured outputs with clear error handling.
- Summary: Small API surface, provider‑agnostic backends, typed outputs by default, and optional tools — compose with normal Python.

LOC comparison (CSV → API payloads)

Raw SDK (conceptual):

```python
import pandas as pd
from openai import OpenAI

client = OpenAI()
df = pd.read_csv("customers.csv")
messages = [{"role": "user", "content": f"Map data {df.head()} to {{fullName, emailAddress}}"}]
resp = client.chat.completions.create(model="gpt-4o", messages=messages)
payloads = json.loads(resp.choices[0].message.content)
```

Alloy:

```python
from alloy import command
import pandas as pd

@command(output=list[dict])
def CSVToAPI(df: pd.DataFrame, example: str) -> str:
    return f"Map data {df.head()} to {example}"

payloads = CSVToAPI(pd.read_csv("customers.csv"), "POST /customers {fullName, emailAddress}")
```

Releases
- Changelog: CHANGELOG.md
- Publishing: Create a tag like `v0.1.1` on main — CI builds and uploads to PyPI (needs Trusted Publishing for `alloy-ai` or a configured token).
