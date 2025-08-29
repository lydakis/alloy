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


@requires_openai
def test_openai_tools_optional_param_is_omittable():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0.1)

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    @command(output=int, tools=[add])
    def use_add() -> str:
        return (
            "Use add(a=2) to compute 2+1. Do not pass b; rely on its default. "
            "Return only the number."
        )

    out = use_add()
    assert isinstance(out, int)
    assert out == 3


@requires_openai
def test_openai_typed_dict_output():
    from typing import TypedDict

    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0.2)

    class Product(TypedDict):
        name: str
        price: float

    @command(output=Product)
    def make() -> str:
        return (
            "Return a Product JSON with name='Test' and price=9.99. "
            "Numbers must be numeric literals (no currency symbols)."
        )

    out = make()
    assert isinstance(out, dict)
    assert out.get("name")
    assert isinstance(out.get("price"), (int, float)) and out["price"] > 0


@requires_openai
@pytest.mark.asyncio
async def test_openai_async_streaming_text_only():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0)
    chunks = []
    aiter = await ask.stream_async("Say 'hello world' exactly once.")
    async for ch in aiter:
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


@requires_openai
def test_openai_sync_streaming_text_only():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0)
    chunks = []
    for ch in ask.stream("Say 'hello world' exactly once."):
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


@requires_openai
@pytest.mark.asyncio
async def test_openai_async_command_streaming_text_only():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0)

    @command(output=str)
    async def gen() -> str:
        return "Say 'streaming ok' in a few words."

    out: list[str] = []
    async for ch in gen.stream():
        out.append(ch)
        if len("".join(out)) >= 5:
            break
    assert len("".join(out)) > 0


@requires_openai
def test_openai_sync_command_streaming_text_only():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0)

    @command(output=str)
    def gen() -> str:
        return "Say 'streaming ok' in a few words."

    out: list[str] = []
    for ch in gen.stream():
        out.append(ch)
        if len("".join(out)) >= 5:
            break
    assert len("".join(out)) > 0
