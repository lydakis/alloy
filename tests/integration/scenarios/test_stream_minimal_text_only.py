import os
import pytest

from alloy import ask, configure


pytestmark = [pytest.mark.integration, pytest.mark.serial]


def _has_any_provider_key() -> bool:
    return any(os.getenv(k) for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"))


@pytest.mark.skipif(not _has_any_provider_key(), reason="No provider API key; integration skipped")
def test_stream_minimal_text_only():
    model = os.getenv("ALLOY_IT_MODEL", os.getenv("ALLOY_MODEL", "gpt-5-mini"))
    configure(model=model, temperature=0.0)
    chunks = []
    for ch in ask.stream("Say a single short sentence about AI."):
        chunks.append(ch)
        if len("".join(chunks)) > 10:
            break
    assert len("".join(chunks)) > 0
