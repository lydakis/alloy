# Contracts

Audience: developers enforcing pre/post conditions around tools and workflows.
Outcome: apply `@require` and `@ensure` to guide the model and catch issues early.
Time: 5 minutes
Prereqs: Python 3.10+, `pip install alloy-ai`.

---

Background: Contracts in Alloy follow [Design by Contract (DbC)](https://en.wikipedia.org/wiki/Design_by_contract) — a software correctness methodology where components declare preconditions and postconditions.

!!! info "DbC in Alloy"
    - `@require`: preconditions checked before a tool runs (receives `inspect.BoundArguments`).
    - `@ensure`: postconditions checked after a tool runs (receives the tool’s result).
    - On failure, Alloy surfaces the contract message back to the model as the tool’s output (not a hard exception) so the model can adjust (e.g., call a prerequisite or fix args).
    - Raise normal exceptions for non‑contract failures you want to stop the workflow; Alloy will surface a brief error back to the model.

## Require (preconditions)

`@require(predicate, message)` runs before the tool. The predicate receives `inspect.BoundArguments`.

```python
from alloy import tool, require

@tool
@require(lambda ba: ba.arguments.get("x", 0) >= 0, "x must be non-negative")
def sqrt_floor(x: int) -> int:
    import math
    return int(math.sqrt(x))
```

## Ensure (postconditions)

`@ensure(predicate, message)` runs after the tool with the tool’s result.

```python
from alloy import tool, ensure

@tool
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    return True
```

## Workflow example

```python
import datetime
from alloy import command, tool, require, ensure

@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "Must add validated_at")
def validate_data(data: dict) -> dict:
    d = dict(data)
    d["validated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return d

@tool
@require(lambda ba: "validated_at" in ba.arguments.get("data", {}), "Run validate_data first")
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    return True

@command(output=str, tools=[validate_data, save_to_production])
def process_order(order: dict) -> str:
    return f"Validate then save this order: {order}"
```

Behavior: on contract failure, Alloy surfaces the message back to the model as the tool’s result (not a hard exception) so the model can adjust (e.g., call a prerequisite) — keeping the loop recoverable and explicit.

Further reading
- [Design by Contract (Wikipedia)](https://en.wikipedia.org/wiki/Design_by_contract)
