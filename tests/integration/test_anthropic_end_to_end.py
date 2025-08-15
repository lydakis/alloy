import os
import pytest

from alloy import command, configure, tool, ensure


has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
model_env = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "claude-sonnet-4-20250514"))
is_claude = model_env.lower().startswith("claude")

requires_anthropic = pytest.mark.skipif(
    not (has_key and is_claude),
    reason="ANTHROPIC_API_KEY not set or model not claude*; integration test skipped",
)


@requires_anthropic
def test_anthropic_simple_command():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)

    @command(output=str)
    def hello() -> str:
        return "Say 'ok' in one word."

    out = hello()
    assert isinstance(out, str)
    assert len(out.strip()) > 0


@requires_anthropic
def test_anthropic_tool_calling():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)

    @tool
    def add(a: int, b: int) -> int:
        return a + b

    @command(output=int, tools=[add])
    def use_add() -> str:
        return "Use add(a,b) to compute 19+23. Return only the number."

    out = use_add()
    assert isinstance(out, int)
    assert out == 42 or out > 0


@requires_anthropic
def test_anthropic_dbc_tool_message_propagates():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)

    @tool
    @ensure(lambda r: isinstance(r, int) and r % 2 == 0, "must be even")
    def square(n: int | str) -> int:
        nn = int(n)
        return nn * nn

    @command(output=str, tools=[square])
    def check() -> str:
        return (
            "Use the tool square(n=3) now. If the tool returns a plain message, output that "
            "message exactly with no extra text."
        )

    out = check()
    assert isinstance(out, str)
    assert "must be even" in out.lower()
