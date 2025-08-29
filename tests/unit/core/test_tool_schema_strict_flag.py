import pytest

pytestmark = pytest.mark.unit


def test_tool_schema_respects_defaults_simple():
    from alloy import tool

    @tool
    def process(data: str, timeout: int = 30):
        return {"ok": True}

    schema = process.spec.as_schema()
    params = schema["parameters"]
    assert params.get("type") == "object"
    assert params.get("required") == ["data"]
    props = params.get("properties") or {}
    assert "data" in props and "timeout" in props


def test_tool_schema_respects_defaults_nested_dataclass():
    from dataclasses import dataclass, field as dc_field
    from alloy import tool
    from alloy.types import to_json_schema

    @dataclass
    class Config:
        name: str
        timeout: int = 30
        retries: int = 3
        tags: list[str] = dc_field(default_factory=list)

    @tool
    def deploy(config: Config):
        return True

    schema = deploy.spec.as_schema()
    cfg_schema = schema["parameters"]["properties"]["config"]
    assert cfg_schema.get("type") == "object"
    assert set(cfg_schema.get("required", [])) == {"name"}

    # Also verify direct call with strict=False yields same
    cfg2 = to_json_schema(Config, strict=False)
    assert cfg2 and set(cfg2.get("required", [])) == {"name"}
