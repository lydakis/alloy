from alloy.config import get_config


def test_env_overrides_model(monkeypatch):
    monkeypatch.setenv("ALLOY_MODEL", "env-model-123")
    # Ensure fresh import not required; get_config reads env each call
    cfg = get_config()
    assert cfg.model == "env-model-123"


def test_env_overrides_temperature_and_tokens(monkeypatch):
    monkeypatch.setenv("ALLOY_TEMPERATURE", "0.25")
    monkeypatch.setenv("ALLOY_MAX_TOKENS", "512")
    cfg = get_config()
    assert cfg.temperature == 0.25
    assert cfg.max_tokens == 512


def test_env_system_and_retry(monkeypatch):
    monkeypatch.setenv("ALLOY_SYSTEM", "You are helpful")
    monkeypatch.setenv("ALLOY_RETRY", "3")
    monkeypatch.setenv("ALLOY_MAX_TOOL_TURNS", "2")
    cfg = get_config()
    assert cfg.default_system == "You are helpful"
    assert cfg.retry == 3
    assert cfg.max_tool_turns == 2
