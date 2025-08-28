import os
import pytest
from dataclasses import dataclass

from alloy import command, configure


pytestmark = [pytest.mark.integration, pytest.mark.serial]


def _has_any_provider_key() -> bool:
    return any(os.getenv(k) for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"))


@pytest.mark.skipif(not _has_any_provider_key(), reason="No provider API key; integration skipped")
def test_structured_output_dataclass():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
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

