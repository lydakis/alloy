import os
import importlib.util
import pytest

from alloy import command, configure, tool, ConfigurationError

pytestmark = pytest.mark.integration


has_ollama = importlib.util.find_spec("ollama") is not None
model_env = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", ""))
is_ollama = model_env.lower().startswith("ollama") or model_env.lower().startswith("local")

requires_ollama = pytest.mark.skipif(
    not (has_ollama and is_ollama),
    reason="Ollama SDK not installed or model not ollama*; integration test skipped",
)


@requires_ollama
def test_ollama_placeholder_tools_not_supported():
    configure(model=model_env or "ollama:gpt-oss", temperature=0.1)

    @tool
    def add(a: int, b: int = 1) -> int:
        return a + b

    @command(output=int, tools=[add])
    def use_add() -> str:
        return "Compute 2+1 using add(a=2); return the number only."

    with pytest.raises(ConfigurationError):
        _ = use_add()


@requires_ollama
def test_ollama_typed_dict_not_supported_raises_commanderror():
    from alloy import CommandError

    configure(model=model_env or "ollama:gpt-oss", temperature=0.1)

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

    with pytest.raises(CommandError):
        _ = make()
