import os
import pytest

from alloy import command, configure, tool


has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
model_env = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", ""))
is_claude = model_env.lower().startswith("claude")

requires_anthropic = pytest.mark.skipif(
    not (has_key and is_claude),
    reason="ANTHROPIC_API_KEY not set or model not claude*; integration test skipped",
)


@requires_anthropic
def test_anthropic_simple_command():
    configure(model=model_env or "claude-3.5-sonnet", temperature=0.2)

    @command(output=str)
    def Hello() -> str:
        return "Say 'ok' in one word."

    out = Hello()
    assert isinstance(out, str)
    assert len(out.strip()) > 0


@requires_anthropic
def test_anthropic_tool_calling():
    configure(model=model_env or "claude-3.5-sonnet", temperature=0.2)

    @tool
    def add(a: int, b: int) -> int:
        return a + b

    @command(output=int, tools=[add])
    def UseAdd() -> str:
        return "Use add(a,b) to compute 19+23. Return only the number."

    out = UseAdd()
    assert isinstance(out, int)
    assert out == 42 or out > 0

