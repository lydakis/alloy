from __future__ import annotations

import json
import typing as t
from dataclasses import is_dataclass, fields, MISSING


Primitive = t.Union[str, int, float, bool]


def to_json_schema(tp: t.Any) -> t.Optional[dict]:
    """Best-effort JSON schema for a Python type.

    Returns None if unstructured.
    """
    origin = t.get_origin(tp)
    args = t.get_args(tp)

    if tp in (str, int, float, bool):
        return {"type": _primitive_name(tp)}

    if tp is None or tp is t.Any:
        return None

    if origin in (list, t.List):
        item = args[0] if args else t.Any
        item_schema = to_json_schema(item) or {}
        return {"type": "array", "items": item_schema}

    if origin in (dict, t.Dict):
        # Generic dicts are unstructured
        return {"type": "object"}

    if is_dataclass_type(tp):
        props = {}
        required = []
        for f in fields(tp):
            f_schema = to_json_schema(f.type) or {}
            props[f.name] = f_schema
            if f.default is MISSING and f.default_factory is MISSING:  # type: ignore[attr-defined]
                required.append(f.name)
        schema = {"type": "object", "properties": props}
        if required:
            schema["required"] = required
        return schema

    # Fallback: unstructured
    return None


def parse_output(tp: t.Any, raw: str) -> t.Any:
    """Parse model output into the desired type.

    Strategy:
      - If schema is primitive or dataclass/array/object -> try JSON first
      - Fallback to best-effort casting for primitives
    """
    schema = to_json_schema(tp)
    # Try JSON first when structured
    if schema is not None:
        try:
            data = json.loads(raw)
            return _coerce(tp, data)
        except Exception:
            pass

    # Primitive coercion
    if tp in (str, int, float, bool):
        return _coerce(tp, raw)

    # Unknown -> return raw
    return raw


def _coerce(tp: t.Any, value: t.Any) -> t.Any:
    origin = t.get_origin(tp)
    args = t.get_args(tp)

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
        kwargs = {}
        for f in fields(tp):
            if f.name in value:
                kwargs[f.name] = _coerce(f.type, value[f.name])
        return tp(**kwargs)

    if origin in (list, t.List) and isinstance(value, list):
        item_tp = args[0] if args else t.Any
        return [
            _coerce(item_tp, v) if item_tp is not t.Any else v for v in value
        ]

    if origin in (dict, t.Dict) and isinstance(value, dict):
        key_tp = args[0] if args else t.Any
        val_tp = args[1] if len(args) > 1 else t.Any
        return {
            (_coerce(key_tp, k) if key_tp is not t.Any else k): (
                _coerce(val_tp, v) if val_tp is not t.Any else v
            )
            for k, v in value.items()
        }

    return value


def is_dataclass_type(tp: t.Any) -> bool:
    try:
        return is_dataclass(tp)  # type: ignore[arg-type]
    except Exception:
        return False


def _primitive_name(tp: t.Any) -> str:
    return {str: "string", int: "integer", float: "number", bool: "boolean"}[tp]

