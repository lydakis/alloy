from __future__ import annotations

import os
from pathlib import Path

import pytest

from alloy import file_search, py_eval, py_exec
from alloy.errors import ToolError


def test_file_search_finds_snippet(tmp_path: Path) -> None:
    p = tmp_path / "notes.txt"
    p.write_text("Alloy makes typed AI commands easy. Deterministic + intelligent.")
    hits = file_search("typed AI", paths=[str(tmp_path)], max_files=3)
    assert isinstance(hits, list) and hits
    assert hits[0]["path"].endswith("notes.txt")
    assert "typed AI".lower() in hits[0]["snippet"].lower()


def test_file_search_validates_inputs(tmp_path: Path) -> None:
    with pytest.raises(ToolError):
        file_search("", paths=[str(tmp_path)])
    with pytest.raises(ToolError):
        file_search("hello", paths=[])


def test_py_eval_basic_math() -> None:
    out = py_eval("2 + 2")
    assert out.strip() == "4"


def test_py_eval_blocks_imports() -> None:
    with pytest.raises(ToolError):
        py_eval("__import__('os').system('echo hi')")


def test_py_exec_captures_output() -> None:
    code = "print(3*3)\nfor i in range(2):\n    print(i)"
    out = py_exec(code)
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert lines == ["9", "0", "1"]


def test_py_exec_blocks_imports() -> None:
    with pytest.raises(ToolError):
        py_exec("import os\nprint(os.listdir('.'))")

