import json
import time
from dataclasses import dataclass
import pytest

from alloy.types import parse_output, to_json_schema


pytestmark = pytest.mark.bench


def test_large_json_parsing_performance():
    @dataclass
    class Entry:
        a: int
        b: float
        c: str

    payload = [{"a": i, "b": i + 0.5, "c": str(i)} for i in range(300)]
    raw = json.dumps(payload)
    tp = list[Entry]

    t0 = time.perf_counter()
    out = parse_output(tp, raw)
    dt = time.perf_counter() - t0
    assert isinstance(out, list) and len(out) == 300
    assert dt < 0.5


def test_schema_generation_many_calls_fast():
    @dataclass
    class Inner:
        n: int
        s: str

    @dataclass
    class Outer:
        x: Inner
        items: list[int]

    t0 = time.perf_counter()
    for _ in range(200):
        _ = to_json_schema(Outer)
    dt = time.perf_counter() - t0
    assert dt < 0.4
