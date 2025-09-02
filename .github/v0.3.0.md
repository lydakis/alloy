# Alloy v0.3.0 — Provider Parity, Finalize Centralization, Streaming Cleanup

Release date: 2025-09-02

Highlights
- Finalize centralization: One canonical rule in `should_finalize_structured_output` handles strings (including wrapped primitives) vs. non-strings. Providers defer to it.
  - For string outputs, finalize only when the text is empty (no extra follow-up turn for non-empty text).
  - For non-strings, finalize when the text is empty or invalid JSON (after stripping code fences).
- Ollama (headline): Dual API support
  - Native `/api/chat` (Ollama SDK) and OpenAI‑compatible Chat Completions (`openai_chat`).
  - Auto‑routes `ollama:*gpt-oss*` to `openai_chat` unless overridden via `extra["ollama_api"]`.
  - Tools supported in both paths; native path supports strict `format={JSON Schema}` for structured outputs.
- Shared helpers across providers:
  - `build_tools_common` for uniform tool-schema building.
  - `ensure_object_schema` to wrap primitives into `{ "value": <primitive> }` consistently.
  - `serialize_tool_payload` to stringify tool results/errors uniformly.
- Config extras normalization (generic-first):
  - Use `tool_choice`, `allowed_tools`, `disable_parallel_tool_use`, `ollama_api`.
  - Provider-prefixed fallbacks remain supported: `openai_tool_choice`, `anthropic_tool_choice`, `anthropic_disable_parallel_tool_use`, `gemini_tool_choice`, `gemini_allowed_tools`, `ollama_tool_choice`.
- Provider parity & cleanup:
  - Client getters standardized as `_get_sync_client` / `_get_async_client`.
  - Streaming: robust resource cleanup (close/aclose) for Gemini and Ollama streams; OpenAI/Anthropic already use context managers.
  - Anthropic: skip JSON prefill after tool errors so plain tool messages surface (e.g., DBC contract messages).
  - Ollama: remove broad exception wrapping in `complete()`; runtime errors now propagate consistently.

Docs
- Configuration guide: provider extras presented as tables; clarified finalize behavior and text-only streaming policy.
- Production guide: clarified error surfaces (ConfigurationError, CommandError, ToolError, ToolLoopLimitExceeded) and retry semantics.
- What’s New updated with a concise, ordered 0.3.0 section.

Tests
- Updated provider tests to patch new client getters (`_get_sync_client`), replacing legacy `_get_client` patches.
- Added unit tests for `ensure_object_schema` and `build_tools_common`.
- Preserved OpenAI async-parallel tools behavior: two calls total (function calls, then final text) for output=str.

Breaking or notable changes
- Internal/test APIs: prefer `_get_sync_client` / `_get_async_client` when patching/mocking provider clients.
- Configuration: prefer generic keys (`tool_choice`, `allowed_tools`, `disable_parallel_tool_use`, `ollama_api`). Provider-prefixed keys remain as fallbacks but may be removed in a future minor.
- Finalize behavior: string outputs across providers no longer trigger a follow-up finalize when non-empty; expect fewer unnecessary follow-up turns.

Upgrade notes
- If you mock providers in tests, update patches to `_get_sync_client`/`_get_async_client`.
- Use generic extras as the primary interface in `Config.extra` or `ALLOY_EXTRA_JSON`.
- For typed outputs that previously returned raw primitives from some providers (e.g., Gemini), outputs now uniformly return JSON objects at the schema level (e.g., `{ "value": 123 }`) and are parsed by Alloy into your requested Python types.

Acknowledgements
- Thanks to everyone who reported parity gaps and helped validate the finalize and streaming changes.
