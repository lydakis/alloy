from __future__ import annotations

from alloy.models.base import ensure_object_schema, build_tools_common
from alloy import tool


def test_ensure_object_schema_wraps_primitives():
    assert ensure_object_schema(None) is None
    assert ensure_object_schema("not-a-dict") is None  # type: ignore[arg-type]

    obj = {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]}
    assert ensure_object_schema(obj) == obj

    wrapped_s = ensure_object_schema({"type": "string"})
    assert isinstance(wrapped_s, dict)
    assert wrapped_s.get("type") == "object"
    props = wrapped_s.get("properties") or {}
    assert "value" in props

    wrapped_n = ensure_object_schema({"type": "number"})
    assert isinstance(wrapped_n, dict)
    assert wrapped_n.get("type") == "object"


def test_build_tools_common_minimal():
    @tool
    def add(a: int, b: int) -> int:
        return a + b

    def fmt(name: str, description: str, params: dict) -> dict:
        return {"name": name, "params": params}

    defs, tmap = build_tools_common([add], fmt)
    assert isinstance(defs, list) and len(defs) == 1
    assert isinstance(tmap, dict) and "add" in tmap
    assert isinstance(defs[0], dict)
    assert defs[0]["name"] == "add"
    assert isinstance(defs[0]["params"], dict)
