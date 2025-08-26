"""
Multiple tools in one call (potential parallel use)

Run:
  python examples/30-tools/03_parallel_tools.py

Notes:
  - Models may call multiple tools; providers can execute them in parallel
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import tool, command, configure
from dotenv import load_dotenv


@tool
def fetch_user_profile(user_id: str) -> dict:
    """Return a mock user profile."""
    return {"user_id": user_id, "name": "Jamie", "plan": "pro"}


@tool
def fetch_user_orders(user_id: str) -> list[dict]:
    """Return recent orders for the user."""
    return [
        {"order_id": "A100", "total": 49.99},
        {"order_id": "A101", "total": 19.5},
    ]


@command(tools=[fetch_user_profile, fetch_user_orders])
def compile_customer_report(user_id: str) -> str:
    return f"""
    Build a short customer report by calling:
    - fetch_user_profile(user_id)
    - fetch_user_orders(user_id)
    Combine results and present a concise summary.
    User: {user_id}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)
    report = compile_customer_report("u-123")
    print(report)


if __name__ == "__main__":
    main()
