## v0.2.2 — Shared loop, Gemini alignment, streaming fix

Highlights:
- Centralized tool loop via `BaseLoopState`; OpenAI (Responses), Anthropic, and Gemini migrated. Gemini now always uses the shared loop.
- `ask.stream_async()` returns an `AsyncIterable[str]` directly (no await at call site).
- Structured outputs: providers finalize only when `auto_finalize_missing_output=True` (default on). Turn‑limit semantics and text‑only streaming preserved.
- OpenAI: ignore `temperature` for reasoning models (`gpt‑5`, `o1`, `o3`); a debug log is emitted when dropped.
- Fake backend: fills nested required properties for stricter strict‑mode parity.

Docs:
- Contributor note on the shared loop and `BaseLoopState` contract (Architecture → Provider Abstraction).
- Streaming guide warning for text‑only streaming.
- Configuration: provider extras and finalize behavior clarified.

No breaking API changes.
