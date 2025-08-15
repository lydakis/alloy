# What's New

Release notes and highlights. See full changelog for details.

- Changelog: https://github.com/lydakis/alloy/blob/main/CHANGELOG.md
- Releases: https://github.com/lydakis/alloy/releases

## 0.1.4 (2025-08-14)
- Typing defaults: omit `output` → `str` (async → `Awaitable[str]`); refined stubs and preserved ParamSpec; `ask.stream_async` typed.
- DBC: `ToolError` messages surface back to the model (OpenAI/Anthropic) for early corrective feedback; unit + integration tests; docs + examples.
- Docs: Typing page, Equivalence Guide, Tool Recipes, patterns examples; standardized imports and decorator style.
- Tooling: pre-commit enforcement for imports and decorator style in code + docs.
