from dataclasses import dataclass
import pytest

from alloy.types import parse_output, to_json_schema


pytestmark = pytest.mark.unit


@dataclass
class Inner:
    n: int
    s: str


@dataclass
class Outer:
    name: str
    items: list[int]
    meta: Inner | None


def test_parse_dataclass_nested_and_unknown_fields_ignored():
    raw = '{"name":"A","items":["1","2"],"meta":{"n":"7","s":"x","junk":1},"extra":"drop"}'
    out = parse_output(Outer, raw)
    assert isinstance(out, Outer)
    assert out.name == "A"
    assert out.items == [1, 2]
    assert isinstance(out.meta, Inner)
    assert out.meta.n == 7 and out.meta.s == "x"


def test_to_json_schema_for_dataclass_has_required_and_no_additional():
    schema = to_json_schema(Outer)
    assert schema and schema.get("type") == "object"
    assert set(schema.get("required", [])) == {"name", "items", "meta"}
    assert schema.get("additionalProperties") is False
