from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import ToolError
from .types import to_json_schema


Predicate = Callable[[Any], bool]


@dataclass
class Contract:
    kind: str
    predicate: Predicate
    message: str


@dataclass
class ToolSpec:
    func: Callable[..., Any]
    name: str
    description: str
    signature: str
    requires: list[Contract] = field(default_factory=list)
    ensures: list[Contract] = field(default_factory=list)

    def as_schema(self) -> dict[str, Any]:
        sig = inspect.signature(self.func)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for name, p in sig.parameters.items():
            if p.annotation is not inspect.Parameter.empty:
                schema = to_json_schema(p.annotation, strict=False)
            else:
                schema = None
            properties[name] = schema if isinstance(schema, dict) else {"type": "string"}
            if p.default is inspect.Parameter.empty:
                required.append(name)
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        }


def require(predicate: Predicate, message: str):
    def deco(fn: Callable[..., Any]):
        _contracts = getattr(fn, "_alloy_require", [])
        _contracts.append(Contract("require", predicate, message))
        setattr(fn, "_alloy_require", _contracts)
        return fn

    return deco


def ensure(predicate: Predicate, message: str):
    def deco(fn: Callable[..., Any]):
        _contracts = getattr(fn, "_alloy_ensure", [])
        _contracts.append(Contract("ensure", predicate, message))
        setattr(fn, "_alloy_ensure", _contracts)
        return fn

    return deco


class ToolCallable:
    def __init__(self, spec: ToolSpec):
        self._spec = spec

    @property
    def spec(self) -> ToolSpec:
        return self._spec

    def __call__(self, *args, **kwargs):
        bound = inspect.signature(self._spec.func).bind_partial(*args, **kwargs)
        bound.apply_defaults()
        for c in self._spec.requires:
            ok = _run_predicate(c.predicate, bound)
            if not ok:
                raise ToolError(c.message)
        result = self._spec.func(*args, **kwargs)
        for c in self._spec.ensures:
            ok = _run_predicate(c.predicate, result)
            if not ok:
                raise ToolError(c.message)
        return result

    def __getattr__(self, item):
        return getattr(self._spec.func, item)


def _run_predicate(pred: Predicate, value: Any) -> bool:
    try:
        return bool(pred(value))
    except Exception:
        return False


def tool(fn: Callable[..., Any] | None = None):
    """Decorator to mark a Python function as an Alloy tool.

    The decorated callable still runs locally in Python, but carries
    metadata and contracts to teach the AI how to use it.
    """

    def wrap(func: Callable[..., Any]):
        requires = list(getattr(func, "_alloy_require", []))
        ensures = list(getattr(func, "_alloy_ensure", []))
        spec = ToolSpec(
            func=func,
            name=func.__name__,
            description=(inspect.getdoc(func) or "").strip(),
            signature=str(inspect.signature(func)),
            requires=requires,
            ensures=ensures,
        )
        wrapped = ToolCallable(spec)
        setattr(wrapped, "_alloy_tool_spec", spec)
        return wrapped

    if fn is not None:
        return wrap(fn)
    return wrap
