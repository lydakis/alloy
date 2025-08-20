from __future__ import annotations

import json
from typing import Any
from typing import get_args, get_origin, get_type_hints
from functools import lru_cache
from dataclasses import is_dataclass, fields


def to_json_schema(tp: Any) -> dict | None:
    """Best-effort JSON Schema generator for output types.

    Supports primitives, dataclasses (with postponed annotations), and nested
    lists/dicts. Falls back to None for complex generics/Unions so callers can
    avoid forcing a schema when not strictly necessary.
    """
    if tp is Any:
        return {"type": "string"}
    if tp in (str, int, float, bool):
        return {"type": _primitive_name(tp)}
    origin = get_origin(tp)
    args = get_args(tp)
    if origin is list:
        items_t = args[0] if args else Any
        items_schema = to_json_schema(items_t) or {"type": "string"}
        return {"type": "array", "items": items_schema}
    if tp is dict or origin is dict:
        raise ValueError(
            "Strict Structured Outputs do not support open-ended dict outputs. "
            "Define a concrete object schema (e.g., a dataclass or TypedDict)."
        )
    if is_dataclass_type(tp):
        props: dict[str, dict] = {}
        required: list[str] = []
        hints = _get_type_hints(tp)
        for f in fields(tp):
            f_type = hints.get(f.name, f.type)
            f_schema = to_json_schema(f_type) or {"type": "string"}
            props[f.name] = f_schema
            required.append(f.name)
        schema = {
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": False,
        }
        return schema

    return None


def parse_output(tp: Any, raw: str) -> Any:
    """Parse model output into the requested type.

    Attempts JSON decoding first, then recursively coerces to the requested type.
    """
    try:
        data = json.loads(raw)
    except Exception:
        data = raw
    schema = to_json_schema(tp)
    if isinstance(data, dict) and "value" in data and schema and schema.get("type") != "object":
        data = data["value"]
    return _coerce(tp, data)


def _coerce(tp: Any, value: Any) -> Any:
    origin = get_origin(tp)
    args = get_args(tp)
    if tp is Any:
        return value
    if tp is str:
        return str(value)
    if tp is int:
        return int(value)
    if tp is float:
        return float(value)
    if tp is bool:
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        return s in ("true", "1", "yes", "y", "t", "on")
    if origin is list:
        if not isinstance(value, list):
            return value
        elem_t = args[0] if args else Any
        return [_coerce(elem_t, v) for v in value]
    if origin is dict:
        if not isinstance(value, dict):
            return value
        key_t = args[0] if len(args) >= 1 else Any
        val_t = args[1] if len(args) >= 2 else Any
        out: dict[Any, Any] = {}
        for k, v in value.items():
            try:
                ck = _coerce(key_t, k)
            except Exception:
                ck = k
            out[ck] = _coerce(val_t, v)
        return out
    if is_dataclass_type(tp) and isinstance(value, dict):
        kwargs: dict[str, Any] = {}
        hints = _get_type_hints(tp)
        for f in fields(tp):
            if f.name in value:
                ft = hints.get(f.name, f.type)
                kwargs[f.name] = _coerce(ft, value[f.name])
        return tp(**kwargs)
    return value


@lru_cache(maxsize=256)
def _get_type_hints(tp: Any) -> dict[str, Any]:
    try:
        return get_type_hints(tp)
    except Exception:
        return {}


def is_dataclass_type(tp: Any) -> bool:
    try:
        return is_dataclass(tp)
    except Exception:
        return False


def _primitive_name(tp: Any) -> str:
    return {str: "string", int: "integer", float: "number", bool: "boolean"}[tp]
