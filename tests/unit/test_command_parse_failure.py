import importlib
import pytest
from alloy import CommandError

pytestmark = [pytest.mark.unit, pytest.mark.errors]


class _StubBackend:
    def complete(self, prompt: str, *, tools=None, output_schema=None, config=None) -> str:
        # Simulate an LLM reply that is not a number
        return "Please provide the text from which you want to extract the price, so I can help you accurately."


def test_command_with_float_output_raises_on_bad_text(monkeypatch):
    # Import the actual submodule to patch its symbol
    cmd_mod = importlib.import_module("alloy.command")
    monkeypatch.setattr(cmd_mod, "get_backend", lambda model: _StubBackend())

    @cmd_mod.command(output=float)
    def extract_price(text: str) -> str:
        return f"Extract the price (number only) from: {text}"

    with pytest.raises(CommandError) as ei:
        _ = extract_price("This item costs $49.99.")

    msg = str(ei.value)
    assert "Failed to parse model output as float" in msg or "failed to parse" in msg.lower()
