import os
import pytest

from alloy import command, ask, configure


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
    # Do not assert exact path (tool vs model), only that it produces a valid int
    assert isinstance(out, int)
    assert out > 0
