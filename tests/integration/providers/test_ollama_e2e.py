import os
import importlib.util
import pytest

from alloy import command, configure

pytestmark = pytest.mark.integration


has_sdk = importlib.util.find_spec("ollama") is not None
model_env = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "ollama:gpt-oss"))
is_ollama = model_env.lower().startswith("ollama:")

requires_ollama = pytest.mark.skipif(
    not (has_sdk and is_ollama),
    reason="Ollama test skipped (need `pip install alloy[ollama]` and ALLOY_IT_MODEL=ollama:<name>)",
)


@requires_ollama
def test_ollama_simple_command():
    configure(model=model_env, temperature=0.2)

    @command(output=str)
    def hello() -> str:
        return "Say 'ok' in one word."

    try:
        out = hello()
    except Exception as e:
        msg = str(e).lower()
        cause = getattr(e, "__cause__", None)
        cmsg = str(cause).lower() if cause else ""
        if ("ollama" in msg or "ollama" in cmsg) and (
            "connect" in msg or "failed" in msg or "connect" in cmsg or "failed" in cmsg
        ):
            pytest.skip(f"Ollama not reachable: {e}")
        raise
    assert isinstance(out, str)
    assert len(out.strip()) > 0
