from dataclasses import dataclass
import json
import pytest

from alloy.types import to_json_schema, parse_output


pytestmark = pytest.mark.unit


@dataclass
class Product:
    name: str
    price: float
    in_stock: bool


def test_roundtrip_dataclass():
    schema = to_json_schema(Product)
    assert schema and schema.get("type") == "object"
    obj = {"name": "T", "price": "9.99", "in_stock": "true", "extra": 1}
    raw = json.dumps(obj)
    p = parse_output(Product, raw)
    assert p.name == "T" and isinstance(p.price, float) and p.in_stock is True
