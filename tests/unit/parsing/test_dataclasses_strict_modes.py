from dataclasses import dataclass, field
import pytest

from alloy.types import to_json_schema


pytestmark = pytest.mark.unit


@dataclass
class Output:
    result: str
    score: float = 0.0


def test_to_json_schema_strict_true_all_fields_required():
    schema = to_json_schema(Output)  # default strict=True
    assert schema and schema.get("type") == "object"
    assert schema.get("required") == ["result", "score"]


@dataclass
class OuterCfg:
    name: str
    retries: int = 3
    flags: list[str] = field(default_factory=list)


def test_to_json_schema_strict_false_respects_defaults():
    schema = to_json_schema(OuterCfg, strict=False)
    assert schema and schema.get("type") == "object"
    assert set(schema.get("required", [])) == {"name"}
