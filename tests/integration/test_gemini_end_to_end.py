import os
import pytest

from alloy import command, configure


has_key = bool(os.getenv("GOOGLE_API_KEY"))
model_env = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gemini-2.5-flash"))
is_gemini = model_env.lower().startswith("gemini")

requires_gemini = pytest.mark.skipif(
    not (has_key and is_gemini),
    reason="GOOGLE_API_KEY not set or model not gemini*; integration test skipped",
)


@requires_gemini
def test_gemini_simple_command():
    configure(model=model_env or "gemini-1.5-pro", temperature=0.2)

    @command(output=str)
    def Hello() -> str:
        return "Say 'ok' in one word."

    out = Hello()
    assert isinstance(out, str)
    assert len(out.strip()) > 0
