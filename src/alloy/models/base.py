from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, AsyncIterable
from typing import Any

from ..config import Config
from ..errors import ConfigurationError
import os, json


class ModelBackend:
    """Abstract provider interface.

    Concrete backends implement completion and tool-calling behavior.
    """

    def complete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        raise NotImplementedError

    def stream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> Iterable[str]:
        raise NotImplementedError

    # Async variants
    async def acomplete(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> str:
        raise NotImplementedError

    async def astream(
        self,
        prompt: str,
        *,
        tools: list | None = None,
        output_schema: dict | None = None,
        config: Config,
    ) -> AsyncIterable[str]:
        raise NotImplementedError


def get_backend(model: str | None) -> ModelBackend:
    if not model:
        raise ConfigurationError(
            "No model configured. Call alloy.configure(model=...) first."
        )
    # Development helper: allow a fake backend for offline/examples via env flag
    if os.environ.get("ALLOY_BACKEND", "").lower() == "fake":
        class _Fake(ModelBackend):
            def complete(self, prompt: str, *, tools=None, output_schema=None, config: Config) -> str:
                if isinstance(output_schema, dict) and output_schema.get("type") == "object":
                    props = output_schema.get("properties", {})
                    obj: dict[str, object] = {}
                    for k, v in props.items():
                        t = v.get("type")
                        if t == "number":
                            obj[k] = 0.0
                        elif t == "integer":
                            obj[k] = 0
                        elif t == "boolean":
                            obj[k] = True
                        elif t == "array":
                            obj[k] = []
                        elif t == "object":
                            obj[k] = {}
                        else:
                            obj[k] = "demo"
                    return json.dumps(obj)
                return "42"
            def stream(self, prompt: str, *, tools=None, output_schema=None, config: Config):
                yield "demo"
            async def acomplete(self, prompt: str, *, tools=None, output_schema=None, config: Config) -> str:
                return self.complete(prompt, tools=tools, output_schema=output_schema, config=config)
            async def astream(self, prompt: str, *, tools=None, output_schema=None, config: Config):
                async def agen():
                    yield "demo"
                return agen()
        return _Fake()
    name = model.lower()
    if name.startswith("gpt") or name.startswith("openai") or "gpt-" in name:
        from .openai import OpenAIBackend

        return OpenAIBackend()

    # Future: route to Anthropic/Gemini/Local or ReAct fallback
    raise ConfigurationError(
        f"No backend available for model '{model}'."
    )
