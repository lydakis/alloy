import os
import importlib.util
import pytest

from alloy import command, configure


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
    def Hello() -> str:
        return "Say 'ok' in one word."

    out = Hello()
    assert isinstance(out, str)
    assert len(out.strip()) > 0
