import os
import pytest
from dataclasses import dataclass

from alloy import command, configure

pytestmark = [pytest.mark.integration, pytest.mark.serial]


def _has_any_provider() -> bool:
    if any(os.getenv(k) for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")):
        return True
    try:
        import importlib.util as _iu

        if _iu.find_spec("ollama") is None:
            return False
        import ollama as _ollama

        _ = _ollama.list()
        return True
    except Exception:
        return False


def _default_model() -> str:
    env_model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", ""))
    if env_model:
        return env_model
    try:
        import importlib.util as _iu

        if _iu.find_spec("ollama") is not None:
            import ollama as _ollama

            _ = _ollama.list()
            return os.getenv("ALLOY_OLLAMA_SCENARIO_MODEL", "ollama:llama3.2")
    except Exception:
        pass
    return "gpt-5-mini"


def _all_available_models() -> list[str]:
    models: list[str] = []
    if os.getenv("OPENAI_API_KEY"):
        models.append(os.getenv("ALLOY_SCENARIOS_OPENAI_MODEL", "gpt-5-mini"))
    if os.getenv("ANTHROPIC_API_KEY"):
        models.append(os.getenv("ALLOY_SCENARIOS_ANTHROPIC_MODEL", "claude-sonnet-4-20250514"))
    if os.getenv("GOOGLE_API_KEY"):
        models.append(os.getenv("ALLOY_SCENARIOS_GEMINI_MODEL", "gemini-2.5-flash"))
    try:
        import importlib.util as _iu

        if _iu.find_spec("ollama") is not None:
            import ollama as _ollama

            _ = _ollama.list()
            models.append(os.getenv("ALLOY_OLLAMA_SCENARIO_MODEL", "ollama:llama3.2"))
    except Exception:
        pass
    return models


def _scenario_models() -> list[str]:
    return _all_available_models() or [_default_model()]


@pytest.mark.skipif(not _has_any_provider(), reason="No provider available; integration skipped")
@pytest.mark.parametrize("model", _scenario_models(), ids=lambda m: m.split(":", 1)[0])
def test_structured_output_dataclass(model: str):
    configure(model=model, temperature=0.0)

    @dataclass
    class Product:
        name: str
        price: float
        in_stock: bool

    @command(output=Product)
    def make() -> str:
        return (
            "Return a Product JSON object only with name='Test', price=9.99, in_stock=true. "
            "Numbers must be numeric literals; no currency symbols."
        )

    p = make()
    assert isinstance(p, Product)
    assert isinstance(p.price, float)
    assert isinstance(p.in_stock, bool)
