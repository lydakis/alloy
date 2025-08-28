# Production

Audience: developers preparing Alloy commands for production use.
Outcome: apply retries/backoff, timeouts, idempotency, logging hooks, and observability patterns.
Time: 6 minutes
Prereqs: Python 3.10+, `pip install alloy-ai`.

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

- `CommandError`: model did not produce a final output or parse failed.
- `ConfigurationError`: invalid output shape or unsupported strict schema.
- Surface exceptions that must stop a workflow; use contracts for recoverable guidance.
