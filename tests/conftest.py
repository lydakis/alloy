import os
import sys
import contextlib
from typing import Any, AsyncIterator, Iterator
import pytest

# Ensure repository root is importable when running tests from subdirectories
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def _reset_alloy_config_state():
    """Reset Alloy global/context config between tests to avoid leakage."""
    from alloy.config import _reset_config_for_tests

    _reset_config_for_tests()
    try:
        yield
    finally:
        _reset_config_for_tests()


class ScriptedFakeBackend:
    """Simple controllable backend for unit/contract tests."""

    def __init__(self) -> None:
        self.next: list[dict[str, Any]] = []

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Any = None,
    ) -> str:
        ev = self.next.pop(0) if self.next else {"type": "text", "data": ""}
        if ev.get("type") == "text":
            return str(ev.get("data", ""))
        raise AssertionError("Unsupported scripted event for .complete()")

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Any = None,
    ) -> Iterator[str]:
        for ev in list(self.next):
            if ev.get("type") == "text_chunk":
                yield str(ev.get("data", ""))

    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Any = None,
    ) -> str:
        return self.complete(prompt, tools=tools, output_schema=output_schema, config=config)

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Any = None,
    ) -> AsyncIterator[str]:
        async def agen() -> AsyncIterator[str]:
            for ev in list(self.next):
                if ev.get("type") == "text_chunk":
                    yield str(ev.get("data", ""))

        return agen()


@pytest.fixture
def fake_backend(monkeypatch: pytest.MonkeyPatch) -> ScriptedFakeBackend:
    """Patch alloy.ask/command to use a shared scripted fake backend."""
    b = ScriptedFakeBackend()
    import importlib

    _cmd_mod = importlib.import_module("alloy.command")
    _ask_mod = importlib.import_module("alloy.ask")
    monkeypatch.setattr(_cmd_mod, "get_backend", lambda model: b)
    monkeypatch.setattr(_ask_mod, "get_backend", lambda model: b)
    return b


@contextlib.contextmanager
def patched_provider(module_path: str, client_attr: str = "Client", client: Any | None = None):
    """Context manager to patch a provider SDK client constructor.

    Example:
        with patched_provider("openai", client_attr="OpenAI", client=my_mock):
            ...
    """
    from unittest.mock import Mock, patch

    with patch(f"{module_path}.{client_attr}", return_value=client or Mock()) as p:
        yield p
