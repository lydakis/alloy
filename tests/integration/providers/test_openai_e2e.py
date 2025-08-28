import os
import pytest

from alloy import command, ask, configure, tool, ensure

pytestmark = pytest.mark.integration


requires_openai = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; integration test skipped",
)


@requires_openai
def test_openai_command_and_ask():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0.2)

    @command(output=float)
    def extract_price(text: str) -> str:
        return f"Extract the numeric price (number only) from: {text}"

    price = extract_price("This item costs $49.99.")
    assert isinstance(price, float)
    assert 0 < price < 1000

    resp = ask("Say OK in one word.")
    assert isinstance(resp, str)
    assert len(resp.strip()) > 0


@requires_openai
def test_openai_tools_minimal():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0.2)

    from alloy import tool

    @tool
    def double(x: int) -> int:
        """Return x * 2."""
        return x * 2

    @command(output=int, tools=[double])
    def use_double() -> str:
        return "Use the provided tool double(x) to compute 21*2. Return only the number."

    out = use_double()
    assert isinstance(out, int)
    assert out > 0


@requires_openai
def test_openai_dbc_tool_message_propagates():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0.2)

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
