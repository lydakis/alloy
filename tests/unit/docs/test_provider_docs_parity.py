from pathlib import Path

import pytest

from alloy.models.anthropic import AnthropicBackend
from alloy.models.gemini import GeminiBackend
from alloy.models.openai import OpenAIBackend
from alloy.models.ollama import OllamaBackend

pytestmark = pytest.mark.unit


def _parse_providers_matrix() -> dict[str, dict[str, str]]:
    path = Path(__file__).resolve().parents[3] / "docs" / "guide" / "providers.md"
    text = path.read_text(encoding="utf-8")
    rows: dict[str, dict[str, str]] = {}
    in_table = False

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(
            "| Provider | Text | Tools | Structured Outputs | Streaming Text | "
            "Streaming + Tools | Streaming + Structured | Notes |"
        ):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            continue

        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 7:
            continue
        provider = parts[0]
        rows[provider] = {
            "text": parts[1],
            "tools": parts[2],
            "structured_outputs": parts[3],
            "streaming_text": parts[4],
            "streaming_tools": parts[5],
            "streaming_structured": parts[6],
        }

    return rows


def _to_bool(v: str) -> bool:
    return v.strip().lower() == "yes"


def test_provider_matrix_matches_backend_streaming_tools():
    table = _parse_providers_matrix()

    expected_backends = {
        "OpenAI": OpenAIBackend(),
        "Anthropic (Claude)": AnthropicBackend(),
        "Google Gemini": GeminiBackend(),
        "Ollama (local)": OllamaBackend(),
    }

    for provider, backend in expected_backends.items():
        assert provider in table, f"Missing row for {provider} in providers matrix"
        row = table[provider]
        assert row["streaming_text"] == "Yes"
        assert (
            _to_bool(row["streaming_tools"]) is bool(backend.supports_streaming_tools)
        )

    # Fake backend is intentionally streaming-text only.
    assert _to_bool(table["Fake (offline)"]["streaming_tools"]) is False

    # Structured output streaming is still not implemented on text stream path.
    assert all(_to_bool(r["streaming_structured"]) is False for r in table.values())


def test_provider_matrix_docs_assert_streaming_structured_not_supported():
    path = Path(__file__).resolve().parents[3] / "docs" / "guide" / "streaming.md"
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "typed/structured streaming is not implemented yet" in lowered
    assert "Text streaming." in text
