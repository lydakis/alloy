from __future__ import annotations

import pytest

from alloy.tool import tool, require, ensure
from alloy.errors import ToolError


def test_require_precondition_receives_args_and_blocks() -> None:
    @tool
    @require(lambda ba: bool(getattr(ba, "arguments", {}).get("x")), "missing x")
    def f(x: int) -> int:
        return x * 2

    # Precondition failure raises ToolError
    with pytest.raises(ToolError) as ei:
        f()  # type: ignore[misc]
    assert "missing x" in str(ei.value)

    # Success path
    assert f(3) == 6


def test_ensure_postcondition_checks_result() -> None:
    @tool
    @ensure(lambda r: isinstance(r, int) and r % 2 == 0, "must be even")
    def g(n: int) -> int:
        return n * n  # odd when n is odd

    with pytest.raises(ToolError) as ei:
        g(3)
    assert "must be even" in str(ei.value)

    assert g(4) == 16
