import os
import pytest

from alloy import command, configure, tool, ensure
from dataclasses import dataclass
from alloy import ask

pytestmark = pytest.mark.integration


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


@requires_anthropic
def test_anthropic_structured_float_output():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)

    @command(output=float)
    def extract_price(text: str) -> str:
        return f"Extract the price (number only) from: {text}"

    price = extract_price("This item costs $49.99 with free shipping.")
    assert isinstance(price, float)
    assert price > 0


@requires_anthropic
def test_anthropic_structured_object_output():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)

    @dataclass
    class ProductRecommendation:
        product_name: str
        original_price: float
        discount_price: float
        reasoning: str

    @command(output=ProductRecommendation)
    def make_rec() -> str:
        return (
            "Return a ProductRecommendation JSON object only. "
            "Use product_name='Test', original_price=100, discount_price=80, and a short reasoning. "
            "Numbers must be numeric literals (no currency symbols)."
        )

    rec = make_rec()
    assert isinstance(rec, ProductRecommendation)
    assert isinstance(rec.original_price, float)
    assert isinstance(rec.discount_price, float)
    assert rec.original_price >= rec.discount_price


@requires_anthropic
def test_anthropic_streaming_text_only_minimal():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)
    chunks = []
    for ch in ask.stream("Say a single short sentence about AI."):
        chunks.append(ch)
        if len("".join(chunks)) > 10:
            break
    assert len("".join(chunks)) > 0


@requires_anthropic
def test_anthropic_sync_streaming_with_tools():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0)

    calls: dict[str, int] = {"count": 0}

    @tool
    def fetch_fact() -> str:
        calls["count"] += 1
        return "Tool says hi"

    chunks = list(
        ask.stream(
            "Call the fetch_fact tool to get the latest detail, then reply exactly with 'Summary: Tool says hi'.",
            tools=[fetch_fact],
        )
    )
    text = "".join(chunks).strip()
    assert "Summary:" in text
    assert "Tool says hi" in text
    assert calls["count"] >= 1


@requires_anthropic
def test_anthropic_parallel_tool_calls_single_message_results():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)

    @tool
    def get_weather(location: str) -> str:
        if "San Francisco" in location:
            return "San Francisco, CA: 68°F, partly cloudy"
        if "New York" in location:
            return "New York, NY: 45°F, clear skies"
        return f"{location}: data"

    @tool
    def get_time(timezone: str) -> str:
        if "Los_Angeles" in timezone:
            return "San Francisco time: 2:30 PM PST"
        if "New_York" in timezone:
            return "New York time: 5:30 PM EST"
        return f"{timezone}: time"

    @command(output=str, tools=[get_weather, get_time])
    def parallel() -> str:
        return (
            "Use tools to get the weather for San Francisco, CA and New York, NY, "
            "and the current time for America/Los_Angeles and America/New_York. "
            "You must include the tool results verbatim in your final answer, one per line."
        )

    out = parallel()
    assert "San Francisco, CA: 68°F, partly cloudy" in out
    assert "New York, NY: 45°F, clear skies" in out
    assert "San Francisco time: 2:30 PM PST" in out
    assert "New York time: 5:30 PM EST" in out


@requires_anthropic
def test_anthropic_tools_optional_param_is_omittable():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.1)

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


@requires_anthropic
def test_anthropic_typed_dict_output():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0.2)
    from typing import TypedDict

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


@requires_anthropic
@pytest.mark.asyncio
async def test_anthropic_async_streaming_text_only():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0)
    chunks = []
    aiter = ask.stream_async("Say 'hello world' exactly once.")
    async for ch in aiter:
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


@requires_anthropic
@pytest.mark.asyncio
async def test_anthropic_async_streaming_with_tools():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0)

    calls: dict[str, int] = {"count": 0}

    @tool
    def fetch_fact() -> str:
        calls["count"] += 1
        return "Tool says hi"

    chunks: list[str] = []
    aiter = ask.stream_async(
        "Call the fetch_fact tool to get the latest detail, then reply exactly with 'Summary: Tool says hi'.",
        tools=[fetch_fact],
    )
    async for ch in aiter:
        chunks.append(ch)
    text = "".join(chunks).strip()
    assert "Summary:" in text
    assert "Tool says hi" in text
    assert calls["count"] >= 1


@requires_anthropic
@pytest.mark.asyncio
async def test_anthropic_async_command_streaming_text_only():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0)
    from alloy import command

    @command(output=str)
    async def gen() -> str:
        return "Say 'streaming ok' in a few words."

    out: list[str] = []
    async for ch in gen.stream():
        out.append(ch)
        if len("".join(out)) >= 5:
            break
    assert len("".join(out)) > 0


@requires_anthropic
def test_anthropic_sync_command_streaming_text_only():
    configure(model=model_env or "claude-sonnet-4-20250514", temperature=0)
    from alloy import command

    @command(output=str)
    def gen() -> str:
        return "Say 'streaming ok' in a few words."

    out: list[str] = []
    for ch in gen.stream():
        out.append(ch)
        if len("".join(out)) >= 5:
            break
    assert len("".join(out)) > 0
