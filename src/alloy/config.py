from __future__ import annotations

from dataclasses import dataclass, field, replace, fields
import os
import json
from typing import Any
import contextvars
import functools
import logging


log = logging.getLogger(__name__)

# Default cap for parallel tool execution across providers
DEFAULT_PARALLEL_TOOLS_MAX: int = 8


@dataclass
class Config:
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    default_system: str | None = None
    retry: int | None = None
    retry_on: type[BaseException] | None = None
    max_tool_turns: int | None = 10
    auto_finalize_missing_output: bool | None = True
    parallel_tools_max: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def merged(self, other: "Config" | None) -> "Config":
        if other is None:
            return self
        updates: dict[str, Any] = {}
        for f in fields(self):
            ov = getattr(other, f.name)
            if ov is None:
                continue
            if f.name == "extra":
                updates["extra"] = {**(self.extra or {}), **(ov or {})}
            else:
                updates[f.name] = ov
        return replace(self, **updates)


_BUILTIN_DEFAULTS: Config = Config(
    model="gpt-5-mini", parallel_tools_max=DEFAULT_PARALLEL_TOOLS_MAX
)
_global_config: Config = Config()
_context_config: contextvars.ContextVar[Config | None] = contextvars.ContextVar(
    "alloy_context_config", default=None
)


def _parse_env_var(name: str, target_type: type) -> Any | None:
    val = os.environ.get(name)
    if val is None:
        return None
    try:
        if target_type is bool:
            return val.strip().lower() in ("1", "true", "yes", "y", "on")
        return target_type(val)
    except (ValueError, TypeError):
        log.warning(
            "Could not parse %s='%s' as %s; ignoring.",
            name,
            val,
            getattr(target_type, "__name__", str(target_type)),
        )
        return None


@functools.lru_cache(maxsize=1)
def _config_from_env() -> Config:
    """Build a Config from process environment variables (cached)."""
    extra: dict[str, Any] = {}
    extra_json = os.environ.get("ALLOY_EXTRA_JSON")
    if extra_json:
        try:
            parsed = json.loads(extra_json)
            if isinstance(parsed, dict):
                extra = parsed
        except json.JSONDecodeError:
            log.warning("Could not parse ALLOY_EXTRA_JSON; must be a JSON object.")
    return Config(
        model=os.environ.get("ALLOY_MODEL") or None,
        temperature=_parse_env_var("ALLOY_TEMPERATURE", float),
        max_tokens=_parse_env_var("ALLOY_MAX_TOKENS", int),
        default_system=(os.environ.get("ALLOY_DEFAULT_SYSTEM") or os.environ.get("ALLOY_SYSTEM")),
        retry=_parse_env_var("ALLOY_RETRY", int),
        retry_on=None,
        max_tool_turns=_parse_env_var("ALLOY_MAX_TOOL_TURNS", int),
        parallel_tools_max=_parse_env_var("ALLOY_PARALLEL_TOOLS_MAX", int),
        auto_finalize_missing_output=_parse_env_var("ALLOY_AUTO_FINALIZE_MISSING_OUTPUT", bool),
        extra=extra,
    )


def configure(**kwargs: Any) -> None:
    """Set global defaults for Alloy execution.

    Example:
        configure(model="gpt-5-mini", temperature=0.7)
    """
    global _global_config
    extra = kwargs.pop("extra", {})
    _global_config = _global_config.merged(Config(extra=extra, **kwargs))


def _reset_config_for_tests() -> None:
    """Internal: reset global/config state for tests.

    Not part of the public API. Avoid using outside tests.
    """
    global _global_config
    _global_config = Config()
    _context_config.set(None)
    try:
        _config_from_env.cache_clear()
    except Exception:
        pass


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
    """Return the effective config with precedence:

    per-call overrides > context > global (configure) > env > built-in defaults
    """
    cfg = (
        _BUILTIN_DEFAULTS.merged(_config_from_env())
        .merged(_global_config)
        .merged(_context_config.get())
    )
    if not overrides:
        ptm = getattr(cfg, "parallel_tools_max", None)
        if not isinstance(ptm, int) or ptm <= 0:
            cfg = replace(
                cfg,
                parallel_tools_max=_BUILTIN_DEFAULTS.parallel_tools_max
                or DEFAULT_PARALLEL_TOOLS_MAX,
            )
        return cfg
    overrides = dict(overrides)
    if "system" in overrides and "default_system" not in overrides:
        overrides["default_system"] = overrides.pop("system")
    extra = overrides.pop("extra", {})
    if isinstance(extra, dict) and extra:
        cfg = cfg.merged(Config(extra=extra))
    allowed = {f.name for f in fields(Config)}
    valid = {k: v for k, v in overrides.items() if k in allowed and v is not None}
    cfg = replace(cfg, **valid)
    ptm2 = getattr(cfg, "parallel_tools_max", None)
    if not isinstance(ptm2, int) or ptm2 <= 0:
        cfg = replace(
            cfg,
            parallel_tools_max=_BUILTIN_DEFAULTS.parallel_tools_max or DEFAULT_PARALLEL_TOOLS_MAX,
        )
    return cfg
