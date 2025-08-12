from __future__ import annotations

import json
import typing as t
from typing import get_args, get_origin
from dataclasses import is_dataclass, fields, MISSING


Primitive = t.Union[str, int, float, bool]


def to_json_schema(tp: t.Any) -> t.Optional[dict]:
    if tp in (str, int, float, bool):
        return {"type": _primitive_name(tp)}
    if is_dataclass_type(tp):
        props: dict[str, dict] = {}
        required: list[str] = []
        for f in fields(tp):
            f_schema = to_json_schema(f.type) or {}
            props[f.name] = f_schema
            if f.default is MISSING and getattr(f, "default_factory", MISSING) is MISSING:
                required.append(f.name)
        schema: dict[str, t.Any] = {"type": "object", "properties": props}
        if required:
            schema["required"] = required
        return schema
    return None


def parse_output(tp: t.Any, raw: str) -> t.Any:
    """Parse model output into the requested type.

    Supports primitives, dataclasses, dict, list, and common generics such as
    list[dict], list[int], dict[str, Any], and list[DataClass]. Falls back to
    returning the raw text when no safe coercion is possible.
    """
    # First, try schema-driven parsing (primitives, dataclasses)
    schema = to_json_schema(tp)
    if schema is not None:
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        # If expecting a primitive and model returned an object {"value": ...}, unwrap
        if tp in (str, int, float, bool) and isinstance(data, dict) and "value" in data:
            data = data["value"]
        return _coerce(tp, data)

    # Handle common typing generics: list[T], dict[K,V]
    origin = get_origin(tp)
    args = get_args(tp)
    if origin is list or origin is t.List:  # type: ignore[attr-defined]
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        if isinstance(data, list):
            elem_t = args[0] if args else t.Any
            return [_coerce(elem_t, v) for v in data]
        return data
    if origin is dict or origin is t.Dict:  # type: ignore[attr-defined]
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        if isinstance(data, dict):
            key_t = args[0] if len(args) >= 1 else t.Any
            val_t = args[1] if len(args) >= 2 else t.Any
            out: dict[t.Any, t.Any] = {}
            for k, v in data.items():
                try:
                    ck = _coerce(key_t, k)
                except Exception:
                    ck = k
                out[ck] = _coerce(val_t, v)
            return out
        return data

    # Primitive text -> primitive
    if tp in (str, int, float, bool):
        return _coerce(tp, raw)
    return raw


def _coerce(tp: t.Any, value: t.Any) -> t.Any:
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
        return s in ("true", "1", "yes", "y")
    if is_dataclass_type(tp) and isinstance(value, dict):
        kwargs: dict[str, t.Any] = {}
        for f in fields(tp):
            if f.name in value:
                kwargs[f.name] = _coerce(f.type, value[f.name])
        return tp(**kwargs)
    return value


def is_dataclass_type(tp: t.Any) -> bool:
    try:
        return is_dataclass(tp)
    except Exception:
        return False


def _primitive_name(tp: t.Any) -> str:
    return {str: "string", int: "integer", float: "number", bool: "boolean"}[tp]
