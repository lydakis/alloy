from __future__ import annotations

from dataclasses import dataclass, field, asdict
import os
import json
from typing import Any
import contextvars


@dataclass
class Config:
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    default_system: str | None = None
    retry: int | None = None
    retry_on: type[BaseException] | None = None
    max_tool_turns: int | None = 2
    auto_finalize_missing_output: bool | None = True
    extra: dict[str, Any] = field(default_factory=dict)

    def merged(self, other: "Config" | None) -> "Config":
        if other is None:
            return self
        # Merge with right precedence: other overrides self
        data = asdict(self)
        other_data = asdict(other)
        merged_extra = {**data.pop("extra"), **other_data.pop("extra")}
        for k, v in other_data.items():
            if v is not None:
                data[k] = v
        data["extra"] = merged_extra
        return Config(**data)


_global_config: Config = Config(model="gpt-5-mini")
_context_config: contextvars.ContextVar[Config | None] = contextvars.ContextVar(
    "alloy_context_config", default=None
)


def _config_from_env() -> Config:
    """Build a Config from process environment variables (optional).

    Supported variables:
      - ALLOY_MODEL (str)
      - ALLOY_TEMPERATURE (float)
      - ALLOY_MAX_TOKENS (int)
      - ALLOY_SYSTEM or ALLOY_DEFAULT_SYSTEM (str)
      - ALLOY_RETRY (int)
      - ALLOY_EXTRA_JSON (JSON object for provider-specific extras)
    """
    model = os.environ.get("ALLOY_MODEL")
    temperature = os.environ.get("ALLOY_TEMPERATURE")
    max_tokens = os.environ.get("ALLOY_MAX_TOKENS")
    system = os.environ.get("ALLOY_DEFAULT_SYSTEM") or os.environ.get("ALLOY_SYSTEM")
    retry = os.environ.get("ALLOY_RETRY")
    max_tool_turns = os.environ.get("ALLOY_MAX_TOOL_TURNS")
    auto_finalize = os.environ.get("ALLOY_AUTO_FINALIZE_MISSING_OUTPUT")
    extra_json = os.environ.get("ALLOY_EXTRA_JSON")

    model_val: str | None = model or None
    temp_val: float | None = None
    if temperature is not None:
        try:
            temp_val = float(temperature)
        except Exception:
            temp_val = None
    max_tokens_val: int | None = None
    if max_tokens is not None:
        try:
            max_tokens_val = int(max_tokens)
        except Exception:
            max_tokens_val = None
    default_system_val: str | None = system or None
    retry_val: int | None = None
    if retry is not None:
        try:
            retry_val = int(retry)
        except Exception:
            retry_val = None
    max_tool_turns_val: int | None = None
    if max_tool_turns is not None:
        try:
            max_tool_turns_val = int(max_tool_turns)
        except Exception:
            max_tool_turns_val = None
    auto_finalize_val: bool | None = None
    if auto_finalize is not None:
        try:
            v = auto_finalize.strip().lower()
            auto_finalize_val = v in ("1", "true", "yes", "y", "on")
        except Exception:
            auto_finalize_val = None
    extra: dict[str, object] = {}
    if extra_json:
        try:
            parsed = json.loads(extra_json)
            if isinstance(parsed, dict):
                extra = parsed
        except Exception:
            pass
    return Config(
        model=model_val,
        temperature=temp_val,
        max_tokens=max_tokens_val,
        default_system=default_system_val,
        retry=retry_val,
        retry_on=None,
        max_tool_turns=max_tool_turns_val,
        auto_finalize_missing_output=auto_finalize_val,
        extra=extra,
    )


def configure(**kwargs: Any) -> None:
    """Set global defaults for Alloy execution.

    Example:
        configure(model="gpt-4", temperature=0.7)
    """
    global _global_config
    extra = kwargs.pop("extra", {})
    _global_config = _global_config.merged(Config(extra=extra, **kwargs))


def use_config(temp_config: Config):
    """Context manager to apply a config within a scope."""

    class _Cfg:
        def __enter__(self):
            self._token = _context_config.set(get_config().merged(temp_config))
            return get_config()

        def __exit__(self, exc_type, exc, tb):
            _context_config.reset(self._token)

    return _Cfg()


def get_config(overrides: dict[str, Any] | None = None) -> Config:
    """Return the effective config (global -> context -> overrides)."""
    cfg = _global_config
    ctx_cfg = _context_config.get()
    if ctx_cfg is not None:
        cfg = cfg.merged(ctx_cfg)
    # Merge process env defaults next, so explicit context/configure override them
    env_cfg = _config_from_env()
    cfg = cfg.merged(env_cfg)
    if overrides:
        # Support alias: `system` -> `default_system` for per-call overrides
        overrides = dict(overrides)  # shallow copy
        if "system" in overrides and "default_system" not in overrides:
            overrides["default_system"] = overrides.pop("system")
        extra = overrides.pop("extra", {})
        cfg = cfg.merged(Config(extra=extra, **overrides))
    return cfg
