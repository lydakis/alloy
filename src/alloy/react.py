"""Simple ReAct fallback stub.

Future: implement a loop that interleaves thoughts, tool calls, and answers
for models without native tool/function calling.
"""

from collections.abc import Iterable

from .config import Config


def react_complete(
    prompt: str,
    *,
    tools: list[dict] | None = None,
    output_schema: dict | None = None,
    config: Config,
) -> str:
    raise NotImplementedError("ReAct fallback not implemented in scaffold")


def react_stream(
    prompt: str,
    *,
    tools: list[dict] | None = None,
    output_schema: dict | None = None,
    config: Config,
) -> Iterable[str]:
    raise NotImplementedError("ReAct streaming not implemented in scaffold")
