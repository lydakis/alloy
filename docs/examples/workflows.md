# Workflows

Assemble small, reliable workflows without a framework (5–8 minutes).

---

## Example

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

print(process_order({"id": 123, "amount": 99.99}))
```

Expected: a short message indicating the steps; contracts guide the model.

## Links (GitHub)
- [Routing/triage](https://github.com/lydakis/alloy/blob/main/examples/50-composition/02_routing_triage.py)
- [Recursive analysis](https://github.com/lydakis/alloy/blob/main/examples/50-composition/03_recursive_analysis.py)
- [Translator network](https://github.com/lydakis/alloy/blob/main/examples/50-composition/04_translator_network.py)
- Folder: [50-composition](https://github.com/lydakis/alloy/tree/main/examples/50-composition)

See also: Guide → Tools & Workflows (guide/tools-and-workflows.md); Guide → Contracts (guide/contracts.md).
