"""
@command with tools

Run:
  python examples/30-tools/02_command_with_tools.py

Notes:
  - Demonstrates passing tools=[...] to a command
  - Offline: export ALLOY_BACKEND=fake
"""

from dataclasses import dataclass
from alloy import tool, command, configure
from dotenv import load_dotenv


CATALOG = [
    {"name": "ProBook 14", "category": "laptop", "price": 999.0, "discount": 10},
    {"name": "ZenPhone X", "category": "phone", "price": 799.0, "discount": 5},
    {"name": "UltraPad 11", "category": "tablet", "price": 649.0, "discount": 0},
    {"name": "LightBook Air", "category": "laptop", "price": 1399.0, "discount": 15},
]


@tool
def search_products(category: str, max_price: float) -> list[dict]:
    """Return products in category under max_price."""
    return [p for p in CATALOG if p["category"] == category and p["price"] <= float(max_price)]


@tool
def apply_discount(price: float, percent: float) -> float:
    """Return price after discount percent."""
    return round(float(price) * (1 - float(percent) / 100), 2)


@dataclass
class Recommendation:
    product: str
    original: float
    discounted: float


@command(output=Recommendation, tools=[search_products, apply_discount])
def recommend(category: str, budget: float) -> str:
    return f"""
    Find the best {category} under ${budget}.
    1) Call search_products(category, budget)
    2) For the top candidate, call apply_discount(price, discount)
    Return Recommendation with product name and both prices.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)
    rec = recommend("laptop", 1200)
    print(rec)


if __name__ == "__main__":
    main()

