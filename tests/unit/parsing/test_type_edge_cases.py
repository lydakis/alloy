from dataclasses import dataclass
from typing import Optional
import pytest

from alloy.types import parse_output


pytestmark = pytest.mark.unit


def test_optional_field_missing_vs_none():
    @dataclass
    class Item:
        a: int
        b: Optional[int] = None

    raw_missing = '{"a": 1}'
    out1 = parse_output(Item, raw_missing)
    assert out1.a == 1 and out1.b is None

    raw_none = '{"a": 2, "b": null}'
    out2 = parse_output(Item, raw_none)
    assert out2.a == 2 and out2.b is None


def test_nested_generic_collections_parse():
    # Nested arrays of ints (supported); open-ended dicts are intentionally disallowed
    tp = list[list[int]]
    raw = '[["1", 2, 3], [4, "5"]]'
    out = parse_output(tp, raw)
    assert out == [[1, 2, 3], [4, 5]]
