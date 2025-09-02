# Models: OpenAI

See also

- Guide → Providers: guide/providers.md
- Architecture → Provider Abstraction: architecture/provider-abstraction.md#provider-mapping

::: alloy.models.openai
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

```bash
export OPENAI_API_KEY=...
export ALLOY_MODEL=gpt-5-mini
```

Note:

- Some reasoning models (e.g., `gpt-5`, `o1`, `o3`) ignore or reject temperature settings. Alloy detects these and does not send `temperature` for such models; a debug log line is emitted when dropped.
