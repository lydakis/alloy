from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import TypedDict
import os, sys

# Ensure project root (with `alloy/`) is importable when running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dotenv import load_dotenv
from alloy import command, tool, require, ensure, configure


# Simple in-memory catalog for demo purposes
class Product(TypedDict):
    name: str
    category: str
    price: float
    discount: int

CATALOG: list[Product] = [
    {"name": "ProBook 14", "category": "laptop", "price": 999.0, "discount": 10},
    {"name": "ZenPhone X", "category": "phone", "price": 799.0, "discount": 5},
    {"name": "UltraPad 11", "category": "tablet", "price": 649.0, "discount": 0},
    {"name": "LightBook Air", "category": "laptop", "price": 1399.0, "discount": 15},
]


@tool
@ensure(lambda r: isinstance(r, list) and len(r) > 0, "Must find at least one product")
def search_products(category: str, budget: str) -> list[Product]:
    """Search demo catalog by category and budget (strings accepted)."""
    try:
        b = float(budget)
    except Exception:
        b = 1e9
    results = [
        p for p in CATALOG if p["category"].lower() == category.lower() and p["price"] <= b
    ]
    return results


@tool
def calculate_discount(price: str, discount_percent: str) -> float:
    """Calculate price after discount. String args are accepted."""
    p = float(price)
    d = float(discount_percent)
    return round(p * (1 - d / 100), 2)


@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "Validation must add timestamp")
def validate_data(data: dict) -> dict:
    """Mark data as validated with timestamp."""
    data = dict(data)
    data["validated_at"] = dt.datetime.utcnow().isoformat()
    return data


@tool
@require(lambda d: isinstance(d, dict) and "validated_at" in d, "Must run validate_data first")
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    """Pretend to save data to production. Returns True on success."""
    # No real DB — return True to simulate success
    return True


@dataclass
class ProductRecommendation:
    product_name: str
    original_price: float
    discount_price: float
    reasoning: str


@command(output=ProductRecommendation, tools=[search_products, calculate_discount, validate_data, save_to_production])
def RecommendProduct(category: str, budget: float) -> str:
    """Find and recommend a product within budget."""
    return f"""
    Task: Recommend the best {category} under ${budget}.
    Tools:
    - search_products(category, budget)
    - calculate_discount(price, discount_percent)
    - validate_data(data) -> adds validated_at
    - save_to_production(data)

    Rules:
    - Always call validate_data on your chosen result once before save.
    - If any tool fails once, do not retry; continue and finalize recommendation.
    - Be concise. Then return ProductRecommendation.
    """


def main():
    load_dotenv()
    # Default model is `gpt-5-mini`; set explicitly for clarity and speed
    # Tip: cap tool iterations with `export ALLOY_MAX_TOOL_TURNS=1` if desired
    configure(model="gpt-5-mini", temperature=0.2, max_tokens=600)

    rec = RecommendProduct("laptop", 1200)
    print("Recommended:", rec.product_name)
    print("Original:", rec.original_price)
    print("Discounted:", rec.discount_price)
    print("Why:", rec.reasoning)


if __name__ == "__main__":
    main()
