"""
Alloy public API.

Python for logic. English for intelligence.

This is an initial scaffold of the v1.0 surface area.
"""

from .command import command
from .tool import tool
from .tool import require, ensure
from .ask import ask
from .config import configure
from .errors import CommandError, ToolError, ConfigurationError, ToolLoopLimitExceeded

__all__ = [
    "command",
    "tool",
    "require",
    "ensure",
    "ask",
    "configure",
    "CommandError",
    "ToolError",
    "ConfigurationError",
    "ToolLoopLimitExceeded",
]
