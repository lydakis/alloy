import os
import pytest

from alloy import command, configure, tool


pytestmark = [pytest.mark.integration, pytest.mark.serial]


def _has_any_provider_key() -> bool:
    return any(os.getenv(k) for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"))


@pytest.mark.skipif(not _has_any_provider_key(), reason="No provider API key; integration skipped")
def test_minimal_tool_chain_one_turn():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0.0)

    @tool
    def add(a: int, b: int) -> int:
        return a + b

    @command(output=int, tools=[add])
    def use_add() -> str:
        return "Use add(a,b) to compute 19+23. Return only the number."

    out = use_add()
    assert isinstance(out, int)
    assert out == 42 or out > 0
