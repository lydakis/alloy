# What's New

Release notes and highlights. See full changelog for details.

- Changelog: https://github.com/lydakis/alloy/blob/main/CHANGELOG.md
- Releases: https://github.com/lydakis/alloy/releases

## 0.1.4 (2025-08-14)
- Typing defaults: omit `output` → `str` (async → `Awaitable[str]`); refined stubs and preserved ParamSpec; `ask.stream_async` typed.
- DBC: `ToolError` messages surface back to the model (OpenAI/Anthropic) for early corrective feedback; unit + integration tests; docs + examples.
- Docs: Typing page, Equivalence Guide, Tool Recipes, patterns examples; standardized imports and decorator style.
- Tooling: pre-commit enforcement for imports and decorator style in code + docs.

## Unreleased
- OpenAI: migrate to Responses API; shared request builder; centralized tool-call processing; safer output assembly.
- Structured Outputs (strict mode):
  - Only provider-enforced JSON Schema; no prompt shaping.
  - Fail fast for open-ended objects (`dict`, `dict[...]`, `list[dict]`) with a clear `ConfigurationError` directing users to a concrete schema (dataclass/TypedDict).
  - Dataclasses: all fields required; `additionalProperties: false`.
- Types: forward-ref dataclass coercion; unified parse path; cached type-hints; native typing.
- Commands: helper mixin for parse/retry; consistent error chaining; retry docs clarified (total attempts).
- Docs: updated “Enforcing Outputs” to describe strict-mode behavior and limitations.
 - Streaming: simplified policy — text-only across providers; commands with tools or non-string outputs do not stream; use provider SDKs for complex streaming.
 - Gemini: backend refactor with non-streaming tool loop and strict finalize; streaming remains text-only.
