import pytest

from alloy.types import to_json_schema, parse_output


pytestmark = pytest.mark.unit


def test_typed_dict_basic_schema_generation():
    from typing import TypedDict

    class UserProfile(TypedDict):
        name: str
        age: int

    schema = to_json_schema(UserProfile)
    assert schema and schema.get("type") == "object"
    props = schema.get("properties") or {}
    req = schema.get("required") or []
    assert set(req) == {"name", "age"}
    assert props.get("name", {}).get("type") == "string"
    assert props.get("age", {}).get("type") == "integer"


def test_typed_dict_total_false_optional_fields():
    from typing import TypedDict

    class OptionalConfig(TypedDict, total=False):
        timeout: int
        retries: int

    # Strict: require all
    schema_strict = to_json_schema(OptionalConfig, strict=True)
    assert set(schema_strict.get("required", [])) == {"timeout", "retries"}
    # Non-strict: none required
    schema_loose = to_json_schema(OptionalConfig, strict=False)
    assert schema_loose.get("required", []) == []


def test_typed_dict_roundtrip_parse():
    from typing import TypedDict

    class Config(TypedDict):
        host: str
        port: int

    schema = to_json_schema(Config)
    assert schema and schema.get("type") == "object"
    raw = '{"host": "localhost", "port": 8080}'
    out = parse_output(Config, raw)
    assert isinstance(out, dict)
    assert out == {"host": "localhost", "port": 8080}


def test_typed_dict_nested():
    from typing import TypedDict

    class Inner(TypedDict):
        value: int

    class Outer(TypedDict):
        name: str
        inner: Inner

    schema = to_json_schema(Outer)
    props = schema.get("properties") or {}
    assert "inner" in props
    inner = props["inner"]
    assert inner.get("type") == "object"
    assert inner.get("properties", {}).get("value", {}).get("type") == "integer"


@pytest.mark.skipif("typing_extensions" not in globals(), reason="typing_extensions not available")
def test_typed_dict_mixed_required_optional_via_notrequired():
    try:
        from typing_extensions import TypedDict, NotRequired
    except Exception:
        pytest.skip("typing_extensions not available")

    class Mixed(TypedDict):
        api_key: str
        endpoint: str
        timeout: NotRequired[int]
        retries: NotRequired[int]

    schema_strict = to_json_schema(Mixed, strict=True)
    assert set(schema_strict.get("required", [])) == {"api_key", "endpoint", "timeout", "retries"}

    schema_loose = to_json_schema(Mixed, strict=False)
    assert set(schema_loose.get("required", [])) == {"api_key", "endpoint"}
