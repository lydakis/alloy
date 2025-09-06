import pytest

from alloy.config import get_config, _reset_config_for_tests
from alloy import command, ConfigurationError

pytestmark = pytest.mark.unit


def test_env_overrides_and_ollama_bridge(monkeypatch):
    _reset_config_for_tests()
    monkeypatch.setenv("ALLOY_MODEL", "ollama:gpt-oss")
    monkeypatch.setenv("ALLOY_TEMPERATURE", "0.5")
    monkeypatch.setenv("ALLOY_MAX_TOKENS", "256")
    monkeypatch.setenv("ALLOY_DEFAULT_SYSTEM", "sys")
    monkeypatch.setenv("ALLOY_PARALLEL_TOOLS_MAX", "0")
    monkeypatch.setenv("ALLOY_AUTO_FINALIZE_MISSING_OUTPUT", "true")
    monkeypatch.setenv("ALLOY_EXTRA_JSON", '{"hint":"x"}')

    cfg = get_config()
    assert (cfg.model or "").lower().startswith("ollama:")
    assert cfg.temperature == 0.5
    assert cfg.max_tokens == 256
    assert cfg.default_system == "sys"
    assert isinstance(cfg.parallel_tools_max, int) and cfg.parallel_tools_max > 0
    assert cfg.extra.get("hint") == "x"
    assert cfg.extra.get("ollama_api") == "openai_chat"


def test_command_stream_rejects_non_string_outputs():
    @command(output=int)
    def foo() -> str:
        return "Say 1"

    with pytest.raises(ConfigurationError):
        list(foo.stream())
