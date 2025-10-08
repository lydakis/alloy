import os

import pytest

from alloy import CommandError, command, configure, tool

pytestmark = pytest.mark.integration


has_key = bool(os.getenv("GOOGLE_API_KEY"))
model_env = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gemini-2.5-flash"))
is_gemini = model_env.lower().startswith("gemini")

requires_gemini = pytest.mark.skipif(
    not (has_key and is_gemini),
    reason="GOOGLE_API_KEY not set or model not gemini*; integration test skipped",
)


def _skip_if_quota_error(exc: CommandError) -> None:
    msg = str(exc).lower()
    if any(tok in msg for tok in ("quota", "rate", "429", "resource exhausted")):
        pytest.skip(f"Gemini quota exhausted: {exc}")


@requires_gemini
def test_gemini_simple_command():
    configure(model=model_env or "gemini-2.5-flash", temperature=0.2)

    @command(output=str)
    def hello() -> str:
        return "Say 'ok' in one word."

    out = hello()
    assert isinstance(out, str)
    assert len(out.strip()) > 0


@requires_gemini
@pytest.mark.asyncio
async def test_gemini_async_streaming_text_only():
    configure(model=model_env or "gemini-2.5-flash", temperature=0)
    from alloy import ask

    chunks = []
    aiter = ask.stream_async("Say 'hello world' exactly once.")
    async for ch in aiter:
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


@requires_gemini
@pytest.mark.asyncio
async def test_gemini_async_streaming_with_tools():
    configure(model=model_env or "gemini-2.5-flash", temperature=0)
    from alloy import ask

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


@requires_gemini
def test_gemini_sync_streaming_text_only():
    configure(model=model_env or "gemini-2.5-flash", temperature=0)
    from alloy import ask

    chunks = []
    for ch in ask.stream("Say 'hello world' exactly once."):
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


@requires_gemini
def test_gemini_sync_streaming_with_tools():
    configure(model=model_env or "gemini-2.5-flash", temperature=0)
    from alloy import ask

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


@requires_gemini
@pytest.mark.asyncio
async def test_gemini_async_command_streaming_text_only():
    configure(model=model_env or "gemini-2.5-flash", temperature=0)
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


@requires_gemini
def test_gemini_sync_command_streaming_text_only():
    configure(model=model_env or "gemini-2.5-flash", temperature=0)
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


@requires_gemini
def test_gemini_tools_optional_param_is_omittable():
    configure(model=model_env or "gemini-2.5-flash", temperature=0.1)

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    @command(output=int, tools=[add])
    def use_add() -> str:
        return (
            "Use add(a=2) to compute 2+1. Do not pass b; rely on its default. "
            "Return only the number."
        )

    try:
        out = use_add()
    except CommandError as exc:
        _skip_if_quota_error(exc)
        raise
    assert isinstance(out, int)
    assert out == 3


@requires_gemini
def test_gemini_typed_dict_output():
    configure(model=model_env or "gemini-2.5-flash", temperature=0.2)
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

    try:
        out = make()
    except CommandError as exc:
        _skip_if_quota_error(exc)
        raise
    assert isinstance(out, dict)
    assert out.get("name")
    assert isinstance(out.get("price"), (int, float)) and out["price"] > 0
