import pytest
from alloy.models.base import should_finalize_structured_output

pytestmark = pytest.mark.unit


def test_finalize_triggers_on_missing_required_top_level():
    schema = {
        "type": "object",
        "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
        "additionalProperties": False,
    }
    assert should_finalize_structured_output("{}", schema) is True
    assert should_finalize_structured_output('{"a":"x","b":1}', schema) is False


def test_finalize_triggers_on_missing_required_nested_array_items():
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"k": {"type": "string"}},
                    "required": ["k"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["items"],
        "additionalProperties": False,
    }
    text_missing = '{"items":[{}]}'
    assert should_finalize_structured_output(text_missing, schema) is True
    text_ok = '{"items":[{"k":"v"}]}'
    assert should_finalize_structured_output(text_ok, schema) is False
