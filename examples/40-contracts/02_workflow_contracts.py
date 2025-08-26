"""
Multi-step workflow with DBC contracts

Run:
  python examples/40-contracts/02_workflow_contracts.py

Notes:
  - @require/@ensure guide model behavior and enforce order
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, tool, require, ensure, configure
from dotenv import load_dotenv
import datetime


@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "Must add validated_at timestamp")
def validate_data(data: dict) -> dict:
    """Add validation timestamp to data."""
    data = dict(data)
    data["validated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
    return data


@tool
@require(
    lambda ba: "validated_at" in ba.arguments.get("data", {}),
    "Run validate_data first",
)
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    """Save validated data to production (mock)."""
    print(f"Saving to production: {data}")
    return True


@command(output=str, tools=[validate_data, save_to_production])
def process_order(order: dict) -> str:
    return f"""
    Process this order through our workflow:
    1. Validate the data (adds timestamp)
    2. Save to production

    Order: {order}

    Return a summary of actions taken.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    order = {"id": 123, "amount": 99.99, "customer": "alice@example.com"}
    result = process_order(order)
    print(result)


if __name__ == "__main__":
    main()

