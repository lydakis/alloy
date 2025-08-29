import os
import pytest

from alloy import command, configure

pytestmark = pytest.mark.integration


has_key = bool(os.getenv("GOOGLE_API_KEY"))
model_env = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gemini-2.5-flash"))
is_gemini = model_env.lower().startswith("gemini")

requires_gemini = pytest.mark.skipif(
    not (has_key and is_gemini),
    reason="GOOGLE_API_KEY not set or model not gemini*; integration test skipped",
)


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
    aiter = await ask.stream_async("Say 'hello world' exactly once.")
    async for ch in aiter:
        chunks.append(ch)
        if len("".join(chunks)) >= 5:
            break
    assert len("".join(chunks)) > 0


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
