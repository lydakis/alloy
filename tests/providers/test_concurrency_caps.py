import concurrent.futures
import json

from alloy.config import Config
from alloy.models.openai import OpenAIBackend
from alloy.models.anthropic import AnthropicBackend
from alloy.models.gemini import GeminiBackend
from alloy import tool


class _FakeFuture:
    def __init__(self, fn, *args, **kwargs):
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def result(self):
        return self._fn(*self._args, **self._kwargs)


class _RecordingPool:
    def __init__(self, max_workers):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def submit(self, fn, *args, **kwargs):
        return _FakeFuture(fn, *args, **kwargs)


@tool
def _echo(x: int = 1) -> int:
    return x


def test_openai_concurrency_cap(monkeypatch):
    be = OpenAIBackend()
    recorded = {}

    def _pool_ctor(max_workers):
        recorded["max_workers"] = max_workers
        return _RecordingPool(max_workers)

    monkeypatch.setattr(concurrent.futures, "ThreadPoolExecutor", _pool_ctor)

    class _Resp:
        def __init__(self, calls_left=True):
            if calls_left:
                self.output = [
                    {"type": "function_call", "name": "_echo", "arguments": json.dumps({"x": i})}
                    for i in range(5)
                ]
            else:
                self.output_text = "done"

    class _Client:
        def __init__(self):
            self.count = 0

        class responses:
            pass

        def responses_create(self, **kwargs):
            self.count += 1
            return _Resp(calls_left=(self.count == 1))

    client = _Client()
    be._client_sync = type(
        "C", (), {"responses": type("R", (), {"create": client.responses_create})()}
    )()

    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)

    cfg = Config(model="gpt-5-mini", parallel_tools_max=3)
    out = be.complete("prompt", tools=[_echo], output_schema=None, config=cfg)
    assert isinstance(out, str)
    assert recorded.get("max_workers") == 3


def test_anthropic_concurrency_cap(monkeypatch):
    be = AnthropicBackend()
    recorded = {}

    def _pool_ctor(max_workers):
        recorded["max_workers"] = max_workers
        return _RecordingPool(max_workers)

    monkeypatch.setattr(concurrent.futures, "ThreadPoolExecutor", _pool_ctor)

    class _Resp:
        def __init__(self, use=True):
            if use:
                self.content = [
                    {"type": "tool_use", "id": f"id{i}", "name": "_echo", "input": {"x": i}}
                    for i in range(5)
                ]
            else:
                self.content = [{"type": "text", "text": "done"}]

    class _Client:
        class messages:
            pass

        def __init__(self):
            self.count = 0

        def messages_create(self, **kwargs):
            self.count += 1
            return _Resp(use=(self.count == 1))

    client = _Client()
    be._client_sync = type(
        "C", (), {"messages": type("M", (), {"create": client.messages_create})()}
    )()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)

    cfg = Config(model="claude-3", parallel_tools_max=2)
    out = be.complete("prompt", tools=[_echo], output_schema=None, config=cfg)
    assert isinstance(out, str)
    assert recorded.get("max_workers") == 2


def test_gemini_concurrency_cap(monkeypatch):
    be = GeminiBackend()
    recorded = {}

    def _pool_ctor(max_workers):
        recorded["max_workers"] = max_workers
        return _RecordingPool(max_workers)

    monkeypatch.setattr(concurrent.futures, "ThreadPoolExecutor", _pool_ctor)

    class _Resp:
        def __init__(self, with_calls=True):
            self.text = ""
            self.function_calls = (
                [
                    type(
                        "FC",
                        (),
                        {"function_call": type("I", (), {"name": "_echo", "args": {"x": i}})()},
                    )
                    for i in range(5)
                ]
                if with_calls
                else []
            )

    class _Client:
        class models:
            pass

        def __init__(self):
            self.count = 0

        def models_generate_content(self, **kwargs):
            self.count += 1
            return _Resp(with_calls=(self.count == 1))

    client = _Client()
    be._client_sync = type(
        "C", (), {"models": type("M", (), {"generate_content": client.models_generate_content})()}
    )()
    monkeypatch.setattr(be, "_get_sync_client", lambda: be._client_sync)

    cfg = Config(model="gemini-2.5-flash", parallel_tools_max=4)
    out = be.complete("prompt", tools=[_echo], output_schema=None, config=cfg)
    assert isinstance(out, str)
    assert recorded.get("max_workers") == 4
