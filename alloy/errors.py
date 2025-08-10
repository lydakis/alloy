class AlloyError(Exception):
    """Base error for Alloy."""


class CommandError(AlloyError):
    """Raised when a command fails to produce a valid result."""


class ToolError(AlloyError):
    """Raised when a tool contract fails or a tool invocation errors."""


class ConfigurationError(AlloyError):
    """Raised when required configuration or provider backends are missing."""

