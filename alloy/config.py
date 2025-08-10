from __future__ import annotations

from dataclasses import dataclass, field, asdict, replace
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
    # Opaque provider-specific kwargs
    extra: dict[str, Any] = field(default_factory=dict)

    def merged(self, other: Optional["Config"]) -> "Config":
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


_global_config: Config = Config()
_context_config: contextvars.ContextVar[Config | None] = contextvars.ContextVar(
    "alloy_context_config", default=None
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
            self._token = _context_config.set(
                get_config().merged(temp_config)
            )
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
    if overrides:
        extra = overrides.pop("extra", {})
        cfg = cfg.merged(Config(extra=extra, **overrides))
    return cfg
