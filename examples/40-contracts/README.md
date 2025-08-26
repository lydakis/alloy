# 40 — Contracts (DBC)

- Purpose: Guard tool behavior with `@require` and `@ensure`.
- When to use: Enforce preconditions, postconditions, and workflows.
- Notes: Failures raise `ToolError` visible to the model for self-correction.
- Offline: `export ALLOY_BACKEND=fake`.

Files:
- `01_require_ensure.py` — minimal contracts
- `02_workflow_contracts.py` — validate → save pipeline
- `03_self_correcting.py` — recover from contract failures
- `04_payment_pipeline.py` — real-world payment flow
