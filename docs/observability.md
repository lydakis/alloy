# Observability

Alloy keeps the core API small and does not add built‑in lifecycle hooks. For most apps, simple wrappers or lightweight callbacks provide sufficient observability.

## Timing wrapper

```python
import time

def with_timing(fn):
    def wrapped(*a, **k):
        t0 = time.time()
        try:
            return fn(*a, **k)
        finally:
            dt = time.time() - t0
            print(f"{fn.__name__} took {dt:.2f}s")
    return wrapped

# apply to a command
generate = with_timing(generate)
```

## Start/stop logging

```python
def log_calls(name):
    def deco(fn):
        def wrapped(*a, **k):
            print(f"→ {name}")
            try:
                return fn(*a, **k)
            finally:
                print(f"← {name}")
        return wrapped
    return deco

@log_calls("extract_price")
def run():
    print(extract_price("$49.99"))
```

## Minimal event capture

Wrap calls in your application layer to record prompts/responses (mind PII):

```python
def capture(fn):
    def wrapped(*a, **k):
        res = fn(*a, **k)
        # send to your logger/trace system
        # logger.info({"fn": fn.__name__, "result": str(res)[:200]})
        return res
    return wrapped
```

## JSON logging (redaction hint)

```python
import json, time

def log_json(event: str, **fields):
    # Redact sensitive fields before logging
    safe = {k: ('[REDACTED]' if k in {'api_key', 'email'} else v) for k, v in fields.items()}
    safe['ts'] = time.time()
    safe['event'] = event
    print(json.dumps(safe))

def run_with_logging(fn):
    def wrapped(*a, **k):
        log_json('start', fn=fn.__name__)
        try:
            out = fn(*a, **k)
            log_json('success', fn=fn.__name__)
            return out
        except Exception as e:
            log_json('error', fn=fn.__name__, error=str(e))
            raise
    return wrapped
```

For production, prefer your existing logging/metrics system around Alloy calls.

See also: [`examples/90-advanced/04_observability.py`](https://github.com/lydakis/alloy/blob/main/examples/90-advanced/04_observability.py) for a minimal timing wrapper.
