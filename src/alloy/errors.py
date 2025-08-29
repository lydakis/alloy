class AlloyError(Exception):
    """Base error for Alloy."""


class CommandError(AlloyError):
    """Raised when a command fails to produce a valid result."""


class ToolError(AlloyError):
    """Raised when a tool contract fails or a tool invocation errors."""


class ConfigurationError(AlloyError):
    """Raised when required configuration or provider backends are missing."""


class ToolLoopLimitExceeded(CommandError):
    """Raised when the tool-call turn limit is exceeded without a final answer.

    Carries additional context for better developer experience.
    """

    def __init__(
        self,
        message: str,
        *,
        max_turns: int | None = None,
        turns_taken: int | None = None,
        partial_text: str | None = None,
    ) -> None:
        super().__init__(message)
        self.max_turns = max_turns
        self.turns_taken = turns_taken
        self.partial_text = partial_text


def create_tool_loop_exception(
    *, max_turns: int | None, turns_taken: int, partial_text: str | None
) -> ToolLoopLimitExceeded:
    """Create a standardized ToolLoopLimitExceeded with contextual details."""
    partial = (partial_text or "").strip()
    msg = f"Exceeded tool-call turn limit (max_tool_turns={max_turns}, turns_taken={turns_taken})."
    if partial:
        msg += f" Partial response: {partial[:500]}"
    else:
        msg += " No final answer produced."
    return ToolLoopLimitExceeded(
        msg, max_turns=max_turns, turns_taken=turns_taken, partial_text=partial_text
    )
