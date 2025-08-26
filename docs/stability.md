# Stability & Support

This project is pre‑1.0. We aim to keep stable areas reliable while iterating quickly elsewhere.

## Public API

- Public modules: `alloy.ask`, `@command`, `@tool`, `require`/`ensure`, `configure`, `Config`, `errors`, `types`.
- Internals: Everything under `alloy.models.*` and other private helpers may change without notice.

## Versioning

- Pre‑1.0: Stable areas avoid breaking changes; other areas may change between minor releases.
- Breaking changes are documented in the changelog with migration guidance when applicable.

## Stability Levels

- Stable: Supported; no breaking changes without deprecation and notice.
- Beta: Reasonably reliable; minor breaking changes possible.
- Experimental: Subject to change; expect breaking changes.

## Providers

- OpenAI: Stable — completions, tools, structured outputs, streaming (no tools‑in‑stream). Note: “Stable” isn’t bug‑free; known issues are tracked and fixes prioritized.
- Anthropic: Beta — completions + tools; streaming (text‑only; no tools/structured outputs in stream).
- Gemini: Experimental — basic completions.
- Ollama: Experimental — basic completions; no structured outputs/tools.

## Features

- Structured outputs: Stable for OpenAI; Beta for Anthropic/Gemini; not applied for Ollama.
- Tools loop: Stable for OpenAI; Beta for Anthropic; Experimental elsewhere.
- Streaming with tools: Not supported (text‑only streaming across providers).

## Support

- Stable areas/providers: Issues prioritized and triaged promptly.
- Beta areas/providers: Best‑effort support.
- Experimental areas/providers: Community‑supported; APIs may change.
