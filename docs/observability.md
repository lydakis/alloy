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

## Demo logging

`examples/tools_demo.py` shows a `DEMO_LOG` environment switch that prints timing for tools:

```bash
DEMO_LOG=1 python examples/tools_demo.py
```

For production, prefer your existing logging/metrics system around Alloy calls.
