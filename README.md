# Alloy (Python)

Python for logic. English for intelligence.

Write typed AI functions that feel like normal Python. Decorate a function with
`@command(output=MyType)`, call any supported model, and get a `MyType` back —
enforced via provider‑native structured outputs. Add Python tools with
design‑by‑contract to keep agent loops reliable.

[![CI](https://github.com/lydakis/alloy/actions/workflows/ci.yml/badge.svg)](https://github.com/lydakis/alloy/actions/workflows/ci.yml)
[![Docs](https://github.com/lydakis/alloy/actions/workflows/docs.yml/badge.svg)](https://docs.alloy.fyi/)
[![Docs Site](https://img.shields.io/badge/docs-website-blue)](https://docs.alloy.fyi/)
[![PyPI](https://img.shields.io/pypi/v/alloy-ai.svg)](https://pypi.org/project/alloy-ai/)
[![Downloads](https://pepy.tech/badge/alloy-ai)](https://pepy.tech/project/alloy-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

License: MIT

Status: see Backends & Routing for current support details: https://docs.alloy.fyi/backends/

## Why Alloy

- Provider‑enforced types: return real Python types (dataclasses, primitives) without brittle string parsing.
- Python‑first: no heavy framework — just functions that compose in your codebase.
- Tools + Contracts: integrate your Python utilities with `@tool` and guard behavior via `@require/@ensure`.
- Predictable defaults: clear errors, capped tool loops (default `max_tool_turns=10`).
- Cross‑provider: same code across OpenAI, Anthropic, Gemini, and Ollama.

## Quick Start

Install (OpenAI only): `pip install alloy-ai`

All providers (OpenAI, Anthropic, Gemini, Ollama): `pip install 'alloy-ai[providers]'`

Set an API key (OpenAI):

```bash
export OPENAI_API_KEY=sk-...
export ALLOY_MODEL=gpt-5-mini   # default if omitted
```

Optional offline mode: `export ALLOY_BACKEND=fake` (deterministic demo outputs)

Hello, Alloy (copy‑paste)

```python
from alloy import ask, command, configure
from dotenv import load_dotenv

load_dotenv(); configure(temperature=0.2)

@command  # returns str by default
def summarize(text: str) -> str:
    return f"Summarize in 1 sentence: {text}"

print(ask("Say hi succinctly."))
print(summarize("Alloy lets you write typed AI functions in Python."))
```

## Flagship Examples

Typed dataclass output (provider‑enforced)

```python
from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv

@dataclass
class ArticleSummary:
    title: str
    key_points: list[str]
    reading_time_minutes: int

@command(output=ArticleSummary)
def summarize_article(text: str) -> str:
    return f"""
    Summarize with: title, 3–5 key_points, reading_time_minutes.
    Article:
    {text}
    """

def main():
    load_dotenv()
    configure(temperature=0.2)
    res = summarize_article("Python emphasizes readability and has a vast ecosystem.")
    print(res)

if __name__ == "__main__":
    main()
```

Tools + DBC (validate → save workflow)

```python
from dotenv import load_dotenv
from alloy import command, tool, require, ensure, configure
import datetime

@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "Must add validated_at")
def validate_data(data: dict) -> dict:
    d = dict(data)
    d["validated_at"] = datetime.datetime.utcnow().isoformat()
    return d

@tool
@require(lambda ba: "validated_at" in ba.arguments.get("data", {}), "Run validate_data first")
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    print("Saving:", data)
    return True

@command(output=str, tools=[validate_data, save_to_production])
def process_order(order: dict) -> str:
    return f"Validate then save this order: {order}"

def main():
    load_dotenv()
    configure(temperature=0.2)
    print(process_order({"id": 123, "amount": 99.99}))

if __name__ == "__main__":
    main()
```

See more: Flagship Examples and the full Examples index in the docs.

- Flagship: https://docs.alloy.fyi/flagship-examples/
- Examples: https://docs.alloy.fyi/examples/

## Streaming policy

- Streaming is text‑only across providers. Commands with tools or non‑string outputs do not stream; call them normally to get typed results.

## Enforcing outputs
- Alloy uses provider‑native structured outputs (JSON Schema) to enforce the expected shape. If parsing fails, you get a clear, typed error.
- Docs: https://docs.alloy.fyi/outputs/

Progressive path
- Start exploratory: `ask("...")`
- Add a command: `@command` → returns `str`
- Enforce types: `@command(output=T)`
- Add tools + DBC: `@command(output=T, tools=[...])` with `@require/@ensure`

Notes
- Streaming with tools is not supported.
- Structured outputs: provider JSON Schema (OpenAI/Anthropic/Gemini) and JSON‑mode guidance for Ollama. See Enforcing outputs above.
- Configuration defaults: `model=gpt-5-mini`; override via `configure(...)` or env.
  - `ALLOY_MODEL`, `ALLOY_TEMPERATURE`, `ALLOY_MAX_TOKENS`, `ALLOY_SYSTEM`/`ALLOY_DEFAULT_SYSTEM`, `ALLOY_RETRY`, `ALLOY_MAX_TOOL_TURNS`.
- OpenAI finalize: if a tool loop completes without a final structured output, Alloy issues one follow‑up turn (no tools) to finalize; then raises if still missing.

Examples
- Explore the runnable suite: https://docs.alloy.fyi/examples/
- Embedded snippets: https://docs.alloy.fyi/flagship-examples/

Offline tip
- For local demos without network/API keys, set `ALLOY_BACKEND=fake` (not for production).

Config precedence (summary)
- Defaults: `model=gpt-5-mini`, `max_tool_turns=10` (safe defaults)
- Process env (ALLOY_*) overrides defaults
- `configure(...)` and context `use_config(...)` override env/defaults
- Per‑call overrides (e.g., `ask(..., model=...)`) override everything above

Make targets
- `make docs-serve` — run docs locally at http://127.0.0.1:8000

 Troubleshooting
- API key: ensure `OPENAI_API_KEY` (or other provider key) is set (env or `.env`)
- Model choice: start with `gpt-5-mini` for speed; override via `configure(model=...)` or `ALLOY_MODEL`
- Slow runs: reduce `max_tokens`, lower `temperature`, prefer smaller models
- Tool loops: default limit is 10; adjust via `configure(max_tool_turns=...)` or `ALLOY_MAX_TOOL_TURNS`
- Errors: read exception messages — Alloy surfaces parse/contract errors clearly

Observability
- See the minimal example: `examples/90-advanced/04_observability.py`. OpenTelemetry integration is planned.

## Support matrix (summary)
- OpenAI (GPT‑4/5 & o‑series): completions, typed commands, ask, streaming (no tools in stream), tool‑calling, structured outputs
- Anthropic (Claude Sonnet/Opus): completions + tool‑calling loop (no streaming yet); requires `max_tokens` (Alloy uses 512 if unset)
- Google (Gemini 2.5 Pro/Flash): completions (tools/streaming limited in scaffold); uses `google‑genai`
- Ollama (local): completions, text streaming, tools via JSON loop, JSON‑mode guidance for typed outputs (`model="ollama:<name>"`)

How to run locally
- Install providers: `pip install 'alloy-ai[providers]'`
- Create `.env` with `OPENAI_API_KEY=...` (or set env vars directly)
- Run any example, e.g.: `python examples/10-commands/01_first_command.py`


Support matrix
- See Backends & Routing for current provider support and stability: https://docs.alloy.fyi/backends/

Install options
- Base: `pip install alloy-ai` (OpenAI + python‑dotenv)
- All providers: `pip install 'alloy-ai[providers]'` (OpenAI, Anthropic, Gemini via `google‑genai`, Ollama)
- Specific extras: `pip install 'alloy-ai[anthropic]'`, `'alloy-ai[gemini]'`, `'alloy-ai[ollama]'`
Documentation
- Full docs: https://docs.alloy.fyi/

Why Alloy vs X

- Minimal, Python‑first: typed outputs + tools without orchestration overhead.
- Cross‑provider: same code, consistent behavior across vendors.
- Clear contracts: DBC tools + strict structured outputs.
- Deep dive: https://docs.alloy.fyi/equivalence/



Releases
- Changelog: CHANGELOG.md
- Publishing: Create a tag like `v0.1.1` on main — CI builds and uploads to PyPI (needs Trusted Publishing for `alloy-ai` or a configured token).
