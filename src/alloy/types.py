from __future__ import annotations

import json
from typing import Any
from typing import get_args, get_origin, get_type_hints, Union as _Union
import types as _pytypes
from functools import lru_cache
from dataclasses import is_dataclass, fields, MISSING


def to_json_schema(tp: Any, strict: bool = True) -> dict | None:
    """Best-effort JSON Schema generator for output types.

    Args:
        tp: The type to convert to JSON schema
        strict: If True (default), all fields are required (for structured outputs).
                If False, fields with defaults are optional (for tool parameters).

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
        items_schema = to_json_schema(items_t, strict=strict) or {"type": "string"}
        return {"type": "array", "items": items_schema}
    if tp is dict or origin is dict:
        if strict:
            raise ValueError(
                "Strict Structured Outputs do not support open-ended dict outputs. "
                "Define a concrete object schema (e.g., a dataclass or TypedDict)."
            )
        return {"type": "object"}
    if is_dataclass_type(tp):
        props: dict[str, dict] = {}
        required: list[str] = []
        hints = _get_type_hints(tp)
        for f in fields(tp):
            f_type = hints.get(f.name, f.type)
            f_schema = to_json_schema(f_type, strict=strict) or {"type": "string"}
            props[f.name] = f_schema
            if strict or (f.default is MISSING and f.default_factory is MISSING):
                required.append(f.name)
        schema = {
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": False,
        }
        return schema

    if is_typeddict_type(tp):
        props_td: dict[str, dict] = {}
        required_td: list[str] = []
        hints = _get_type_hints(tp)
        required_keys = set(getattr(tp, "__required_keys__", set()))
        optional_keys = set(getattr(tp, "__optional_keys__", set()))
        if not required_keys and not optional_keys:
            total = getattr(tp, "__total__", True)
            if total:
                required_keys = set(hints.keys())
            else:
                optional_keys = set(hints.keys())
        for name, f_type in hints.items():
            f_schema = to_json_schema(f_type, strict=strict) or {"type": "string"}
            props_td[name] = f_schema
            if strict or (name in required_keys):
                required_td.append(name)
        return {
            "type": "object",
            "properties": props_td,
            "required": required_td,
            "additionalProperties": False,
        }

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
    if origin in (_Union, getattr(_pytypes, "UnionType", object())):
        if value is None:
            return None
        last_exc: Exception | None = None
        for alt in args:
            if alt is type(None):
                continue
            try:
                return _coerce(alt, value)
            except Exception as e:
                last_exc = e
                continue
        if last_exc is not None:
            raise last_exc
        return value
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
    if is_typeddict_type(tp) and isinstance(value, dict):
        out_td: dict[str, Any] = {}
        hints = _get_type_hints(tp)
        for k, t in hints.items():
            if k in value:
                out_td[k] = _coerce(t, value[k])
        return out_td
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


def is_typeddict_type(tp: Any) -> bool:
    try:
        from typing_extensions import is_typeddict as _is_td

        return bool(_is_td(tp))
    except Exception:
        try:
            return bool(
                hasattr(tp, "__annotations__")
                and hasattr(tp, "__total__")
                and (hasattr(tp, "__required_keys__") or hasattr(tp, "__optional_keys__"))
            )
        except Exception:
            return False


def _primitive_name(tp: Any) -> str:
    return {str: "string", int: "integer", float: "number", bool: "boolean"}[tp]
