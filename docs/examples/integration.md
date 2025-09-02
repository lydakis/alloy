# Integration

Integrate Alloy with common Python libraries and HTTP (6–10 minutes).

---

## Example (pandas)

```python
from alloy import command

@command(output=list[dict])
def csv_to_api(rows: list[dict]) -> str:
    return "Map rows to API shape with keys: fullName, emailAddress, tier"

rows = [{"name": "Ada", "email": "ada@example.com", "plan": "pro"}]
print(csv_to_api(rows))
```

Expected: a list of dicts shaped for your API.

## Links (GitHub)

- [Pandas + command](https://github.com/lydakis/alloy/blob/main/examples/60-integration/01_with_pandas.py)
- [Flask JSON endpoint](https://github.com/lydakis/alloy/blob/main/examples/60-integration/02_flask_endpoint.py)
- Folder: [60-integration](https://github.com/lydakis/alloy/tree/main/examples/60-integration)

## Tips

- Add ImportError guards with clear install tips for optional deps.
- Keep endpoints idempotent; validate inputs and cap token budgets.
