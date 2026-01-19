import os
import json
import pytest
from dataclasses import dataclass

from alloy import command, configure, CommandError
from tests.utils.oracle import extract_price_oracle
from tests.utils.normalization import normalize_price

pytestmark = [pytest.mark.parity_live, pytest.mark.serial]


CASES = [
    ("The total is $19.99 today only!", {"amount": 19.99, "currency": "USD"}),
    ("Τιμή: 3.000,50 €", {"amount": 3000.50, "currency": "EUR"}),
    ("Price: JPY 1200 (tax incl.)", {"amount": 1200.0, "currency": "JPY"}),
    ("£0.99 per month", {"amount": 0.99, "currency": "GBP"}),
    ("USD 1,234", {"amount": 1234.0, "currency": "USD"}),
]


@dataclass
class Price:
    amount: float
    currency: str


@pytest.mark.parametrize(
    "provider,model",
    [
        ("openai", "gpt-5-mini"),
        ("anthropic", "claude-sonnet-4-20250514"),
        ("gemini", "gemini-2.5-flash"),
        ("ollama", os.getenv("ALLOY_OLLAMA_PARITY_MODEL", "ollama:llama3.2")),
    ],
)
@pytest.mark.parametrize("text,_", CASES, ids=[c[0] for c in CASES])
def test_price_parity(provider, model, text, _, monkeypatch):
    req = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }
    if provider == "ollama":
        try:
            import importlib.util as _iu

            if _iu.find_spec("ollama") is None:
                pytest.skip("Ollama SDK not installed")
            import ollama as _ollama

            _ = _ollama.list()
        except Exception:
            pytest.skip("Ollama server not running; set ALLOY_OLLAMA_PARITY_MODEL or start Ollama")
    else:
        key = req.get(provider)
        if key and not os.getenv(key):
            pytest.skip(f"Missing {key}")

    if provider == "ollama":
        configure(
            model=model,
            temperature=0,
            extra={"ollama_api": os.getenv("ALLOY_OLLAMA_API", "native")},
        )
    else:
        configure(model=model, temperature=0)

    @command(output=Price)
    def extract_price(s: str) -> str:
        return f"""
        Extract a price and currency from the text: {s}
        """

    try:
        model_raw = extract_price(text)
    except CommandError as e:
        emsg = str(e).lower()
        if any(tok in emsg for tok in ("quota", "rate", "429")):
            pytest.skip(f"Provider error for {provider}: {e}")
        raise
    model_norm = normalize_price(model_raw)
    oracle_norm = normalize_price(extract_price_oracle(text))

    if model_norm != oracle_norm:
        raise AssertionError(
            json.dumps(
                {
                    "provider": provider,
                    "model": model,
                    "input": text,
                    "model_raw": getattr(model_raw, "__dict__", dict(model_raw=model_raw)),
                    "model_norm": model_norm.__dict__,
                    "oracle": oracle_norm.__dict__,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
