# Production

Prepare Alloy commands for production: retries, timeouts, idempotency, logging, and observability (~6 minutes). Requires Python 3.10+ and `pip install alloy-ai`.

---

## Retries and timeouts

Use global defaults via `configure(...)` or per‑call overrides.

```python
from alloy import configure

configure(retry=2, max_tokens=512)
```

## Idempotency

- Keep tools idempotent where possible; include natural keys in inputs.
- For external side‑effects, design explicit commit steps behind `@ensure`.

## Logging and diagnostics

- Add structured logging around command entry/exit and tool calls.
- Redact secrets/PII in logs (inputs/outputs).

## Observability

- See Observability for JSON logging with redaction hints and an advanced example.
- OpenTelemetry integration is under evaluation and will land post‑RFC.

## Errors

- `ConfigurationError`: misconfiguration or unsupported capability. Examples: missing/invalid model, provider SDK not installed, invalid strict output schema, using streaming with tools/typed outputs.
- `CommandError`: command failed to produce a final value. Examples: model returned empty output; parse failed for the requested type; provider error bubbled up and retries (if any) were exhausted.
- `ToolError`: raised by tools (often via `@require/@ensure`) and surfaced back to the model as the tool's output so it can adjust — not a hard failure by itself.
- `ToolLoopLimitExceeded`: too many tool turns; includes the last partial assistant text to aid recovery.

Retry behavior
- Per-command retries are controlled by `configure(retry=...)` and `retry_on=...`.
- If `retry_on` is unset, all exceptions are retried up to `retry` attempts; if set, only matching exceptions are retried.

Provider error surfaces
- Runtime API errors (e.g., HTTP 4xx/5xx) propagate from providers; the command wrapper converts them into `CommandError` after retries (unless explicitly handled).
- Configuration errors (e.g., SDK missing) are raised as `ConfigurationError` immediately.

Contracts guidance
- Use contracts for recoverable guidance. Surface exceptions that must stop a workflow; avoid overusing exceptions for control flow.
