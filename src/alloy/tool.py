from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .errors import ToolError


Predicate = Callable[[Any], bool]


@dataclass
class Contract:
    kind: str  # "require" | "ensure"
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
        # Minimal function tool schema for provider adapters
        params = inspect.signature(self.func).parameters
        properties = {name: {"type": "string"} for name in params}  # simple stub
        required = list(params.keys())
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
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
        # Bind arguments to run preconditions with access to arguments
        bound = inspect.signature(self._spec.func).bind_partial(*args, **kwargs)
        bound.apply_defaults()
        # REQUIRE checks
        for c in self._spec.requires:
            ok = _run_predicate(c.predicate, bound)
            if not ok:
                raise ToolError(c.message)
        # Call tool
        result = self._spec.func(*args, **kwargs)
        # ENSURE checks
        for c in self._spec.ensures:
            ok = _run_predicate(c.predicate, result)
            if not ok:
                raise ToolError(c.message)
        return result

    # For provider adapters to introspect
    def __getattr__(self, item):  # pragma: no cover - passthrough
        return getattr(self._spec.func, item)


def _run_predicate(pred: Predicate, value: Any) -> bool:
    try:
        return bool(pred(value))
    except Exception:
        return False


def tool(fn: Optional[Callable[..., Any]] = None):
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
        # Attach spec for adapters
        setattr(wrapped, "_alloy_tool_spec", spec)
        return wrapped

    if fn is not None:
        return wrap(fn)
    return wrap

