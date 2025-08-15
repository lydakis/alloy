# Alloy (Python)

Python for logic. English for intelligence.

Alloy lets you declare typed AI commands in Python, wire up tools, and route to multiple model providers with a consistent API.

- Typed commands via `@command(output=...)`
- Simple `ask(...)` namespace for quick prompts
- Tool calling with contracts and validation
- Multi‑provider backends (OpenAI, Anthropic, Gemini, Ollama)

See Getting Started for installation and a 2‑minute tutorial.

> Note: This site is built and deployed via GitHub Actions.

## Philosophy

- Keep primitives small and explicit: typed `@command` and plain‑Python `@tool`.
- Compose behavior in Python (functions, modules, asyncio), not a new orchestration layer.
- Prefer predictable defaults; opt into structure via `output=...`.
- Stay provider‑agnostic; adaptors live under `alloy/models/*`.
- Offer recipes instead of bundled features so teams can choose libraries and guarantees.
