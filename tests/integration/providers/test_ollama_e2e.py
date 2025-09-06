import os
import importlib.util
import pytest

from alloy import command, configure, tool, ensure

pytestmark = pytest.mark.integration


has_ollama = importlib.util.find_spec("ollama") is not None
if has_ollama:
    try:
        import ollama

        _ = ollama.list()
        has_ollama = True
    except Exception:
        has_ollama = False

requires_ollama = pytest.mark.skipif(
    not has_ollama,
    reason="Ollama not available (SDK missing or server not running); integration test skipped",
)
OLLAMA_E2E_PARAMS = [
    ("native", os.getenv("ALLOY_OLLAMA_NATIVE_MODEL", "ollama:llama3.2")),
    ("openai_chat", os.getenv("ALLOY_OLLAMA_OPENAI_MODEL", "ollama:gpt-oss")),
]


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
def test_ollama_tools_execute_e2e(strategy: str, model_id: str):
    configure(model=model_id, temperature=0, extra={"ollama_api": strategy})

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    @command(output=int, tools=[add])
    def use_add() -> str:
        return "Use add(a=2) to compute 2+1. Return only the number."

    out = use_add()
    assert isinstance(out, int) and out > 0


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
def test_ollama_typed_dict_structured_output_e2e(strategy: str, model_id: str):
    configure(model=model_id, temperature=0, extra={"ollama_api": strategy})

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


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
def test_ollama_command_and_ask(strategy: str, model_id: str):
    configure(model=model_id, temperature=0.2, extra={"ollama_api": strategy})

    @command(output=float)
    def extract_price(text: str) -> str:
        return f"Extract the numeric price (number only) from: {text}"

    price = extract_price("This item costs $49.99.")
    assert isinstance(price, float)
    assert 0 < price < 1000

    from alloy import ask

    resp = ask("Say OK in one word.")
    assert isinstance(resp, str) and resp.strip()


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
def test_ollama_tools_optional_param_is_omittable(strategy: str, model_id: str):
    configure(model=model_id, temperature=0.1, extra={"ollama_api": strategy})

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
    assert out == 3 or out > 0


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
def test_ollama_dbc_tool_message_propagates(strategy: str, model_id: str):
    configure(model=model_id, temperature=0.2, extra={"ollama_api": strategy})

    @tool
    @ensure(lambda r: isinstance(r, int) and r % 2 == 0, "pineapple")
    def some_tool(n: int | str) -> int:
        nn = int(n)
        return nn * nn

    @command(output=str, tools=[some_tool])
    def check() -> str:
        return (
            "Use the tool some_tool(n=3) now. If the tool returns a plain message, output that "
            "message exactly with no extra text"
        )

    out = check()
    assert isinstance(out, str)
    assert "pineapple" in out.lower()


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
def test_ollama_sync_streaming_text_only(strategy: str, model_id: str):
    from alloy import ask

    configure(model=model_id, temperature=0, extra={"ollama_api": strategy})
    chunks: list[str] = []
    for ch in ask.stream("Say 'hello world' exactly once."):
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
@pytest.mark.asyncio
async def test_ollama_async_streaming_text_only(strategy: str, model_id: str):
    from alloy import ask

    configure(model=model_id, temperature=0, extra={"ollama_api": strategy})
    chunks: list[str] = []
    aiter = ask.stream_async("Say 'hello world' exactly once.")
    async for ch in aiter:
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
def test_ollama_sync_command_streaming_text_only(strategy: str, model_id: str):
    configure(model=model_id, temperature=0, extra={"ollama_api": strategy})

    @command(output=str)
    def gen() -> str:
        return "Say 'streaming ok' in a few words."

    out: list[str] = []
    for ch in gen.stream():
        out.append(ch)
        if len("".join(out)) >= 5:
            break
    assert len("".join(out)) > 0


@requires_ollama
@pytest.mark.parametrize(("strategy", "model_id"), OLLAMA_E2E_PARAMS)
@pytest.mark.asyncio
async def test_ollama_async_command_streaming_text_only(strategy: str, model_id: str):
    configure(model=model_id, temperature=0, extra={"ollama_api": strategy})

    @command(output=str)
    async def gen() -> str:
        return "Say 'streaming ok' in a few words."

    out: list[str] = []
    async for ch in gen.stream():
        out.append(ch)
        if len("".join(out)) >= 5:
            break
    assert len("".join(out)) > 0


@requires_ollama
def test_ollama_native_tool_dataclass_payload():
    from dataclasses import dataclass

    model_id = os.getenv("ALLOY_OLLAMA_NATIVE_MODEL", "ollama:llama3.2")
    configure(model=model_id, temperature=0, extra={"ollama_api": "native"})

    @dataclass
    class FlightOption:
        airline: str
        price: int

    @tool
    def pick_flight() -> FlightOption:
        """Return a flight option (dataclass)."""
        return FlightOption(airline="TestAir", price=123)

    @command(output=str, tools=[pick_flight])
    def plan() -> str:
        return "Use the tool pick_flight() now. Then respond with 'ok'."

    out = plan()
    assert isinstance(out, str) and out.strip()


@requires_ollama
def test_ollama_openai_chat_tool_dataclass_payload():
    from dataclasses import dataclass

    model_id = os.getenv("ALLOY_OLLAMA_OPENAI_MODEL", "ollama:gpt-oss")
    configure(model=model_id, temperature=0, extra={"ollama_api": "openai_chat"})

    @dataclass
    class FlightOption:
        airline: str
        price: int

    @tool
    def pick_flight() -> FlightOption:
        """Return a flight option (dataclass)."""
        return FlightOption(airline="TestAir", price=123)

    @command(output=str, tools=[pick_flight])
    def plan() -> str:
        return "Use the tool pick_flight() now. Then respond with 'ok'."

    out = plan()
    assert isinstance(out, str) and out.strip()
