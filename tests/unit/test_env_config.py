from alloy.config import get_config, _reset_config_for_tests


def test_env_overrides_model(monkeypatch):
    _reset_config_for_tests()
    monkeypatch.setenv("ALLOY_MODEL", "env-model-123")
    # Ensure fresh import not required; get_config reads env each call
    cfg = get_config()
    assert cfg.model == "env-model-123"


def test_env_overrides_temperature_and_tokens(monkeypatch):
    _reset_config_for_tests()
    monkeypatch.setenv("ALLOY_TEMPERATURE", "0.25")
    monkeypatch.setenv("ALLOY_MAX_TOKENS", "512")
    cfg = get_config()
    assert cfg.temperature == 0.25
    assert cfg.max_tokens == 512


def test_env_system_and_retry(monkeypatch):
    _reset_config_for_tests()
    monkeypatch.setenv("ALLOY_SYSTEM", "You are helpful")
    monkeypatch.setenv("ALLOY_RETRY", "3")
    monkeypatch.setenv("ALLOY_MAX_TOOL_TURNS", "2")
    cfg = get_config()
    assert cfg.default_system == "You are helpful"
    assert cfg.retry == 3
    assert cfg.max_tool_turns == 2


def test_overrides_do_not_reset_max_tool_turns(monkeypatch):
    _reset_config_for_tests()
    # Env sets tool turns to 25; per-call overrides (default_system) must not
    # reset it back to the dataclass default.
    monkeypatch.setenv("ALLOY_MAX_TOOL_TURNS", "25")
    from alloy.config import get_config, configure

    # Configure should take precedence over env.
    configure(model="env-model-override", max_tool_turns=8)
    cfg = get_config({"default_system": "x"})
    assert cfg.max_tool_turns == 8

    # Remove env; per-call overrides still must not reset to the dataclass default (10); should see 8 from configure
    monkeypatch.delenv("ALLOY_MAX_TOOL_TURNS", raising=False)
    cfg2 = get_config({"default_system": "x"})
    assert cfg2.max_tool_turns == 8
