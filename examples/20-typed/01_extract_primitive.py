"""
Primitive typed outputs (float and int)

Run:
  python examples/20-typed/01_extract_primitive.py

Notes:
  - Shows output=float and output=int for precise parsing
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command(output=float)
def extract_price(text: str) -> str:
    """Extract a price as a float (number only)."""
    return f"Return only the numeric price value from: {text}"


@command(output=int)
def count_items(text: str) -> str:
    """Return the number of items mentioned, as an integer."""
    return f"Count the items described and return only an integer: {text}"


def main():
    load_dotenv()
    configure(temperature=0.2)

    p = extract_price("Subtotal $49.99, tax $4.00, total $53.99.")
    n = count_items("We purchased 3 laptops and 2 monitors.")
    print("Price:", p)
    print("Items:", n)


if __name__ == "__main__":
    main()
