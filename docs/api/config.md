# Config

::: alloy.config
    options:
      show_source: false
      show_root_heading: true
      members_order: source
      separate_signature: true

## Usage

```python
from alloy import configure

# Global defaults
configure(model="gpt-5-mini", temperature=0.2, max_tokens=512)

# Per-call overrides take precedence
# ask("...", model="gpt-5-mini", temperature=0.0)
```

Precedence
- 1. Per-call overrides (e.g., `ask(..., model=...)`)
- 2. `configure(...)` and context scopes
- 3. Environment (`ALLOY_*`)
- 4. Built-ins (e.g., `model="gpt-5-mini"`)

!!! note "See also"
    - Guide → Configuration: guide/configuration.md
