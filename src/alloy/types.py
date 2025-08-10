from __future__ import annotations

import json
import typing as t
from dataclasses import is_dataclass, fields, MISSING


Primitive = t.Union[str, int, float, bool]


def to_json_schema(tp: t.Any) -> t.Optional[dict]:
    origin = t.get_origin(tp)
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
    schema = to_json_schema(tp)
    if schema is not None:
        try:
            data = json.loads(raw)
        except Exception:
            data = raw
        return _coerce(tp, data)
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

