from __future__ import annotations

"""
Minimal built-in tools for Alloy.

Philosophy: simple, local-first, and provider-agnostic. These tools are usable
as-is for common tasks and act as reference implementations you can replace or
extend in your own project.
"""

from dataclasses import dataclass
import io
import os
import re
import glob
import math
import contextlib
from typing import Any

from .tool import tool, ToolError


@dataclass
class FileHit:
    path: str
    snippet: str


@tool
def file_search(
    query: str,
    *,
    paths: list[str],
    max_files: int = 5,
    max_chars: int = 240,
) -> list[dict]:
    """Search local text files under given paths and return snippets.

    Args:
        query: Case-insensitive substring to look for.
        paths: List of directories or glob patterns to search.
        max_files: Maximum number of file hits to return.
        max_chars: Max characters for the returned snippet per file.

    Returns:
        A list of {"path": str, "snippet": str} dicts.
    """
    if not query.strip():
        raise ToolError("query must be non-empty")
    if not paths:
        raise ToolError("paths must contain at least one directory or glob pattern")

    patterns: list[str] = []
    for p in paths:
        if os.path.isdir(p):
            patterns.append(os.path.join(p, "**", "*"))
        else:
            patterns.append(p)

    hits: list[FileHit] = []
    needle = query.lower()
    seen: set[str] = set()
    for pat in patterns:
        for fp in glob.iglob(pat, recursive=True):
            if len(hits) >= max_files:
                break
            if not os.path.isfile(fp) or fp in seen:
                continue
            seen.add(fp)
            # Heuristic: only read likely text files
            if os.path.splitext(fp)[1].lower() in {".txt", ".md", ".py", ".rst", ".json"}:
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        data = f.read()
                except Exception:
                    continue
                where = data.lower().find(needle)
                if where != -1:
                    start = max(0, where - max_chars // 4)
                    end = min(len(data), where + len(query) + max_chars // 2)
                    snippet = data[start:end].strip()
                    hits.append(FileHit(path=fp, snippet=snippet))
    return [{"path": h.path, "snippet": h.snippet} for h in hits]


@tool
def web_search(query: str, max_results: int = 3) -> list[dict]:
    """Minimal web search facade (requires configuration).

    By default this tool is inactive to keep Alloy self-contained. To enable,
    install and configure a search provider and adapt this function accordingly.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        A list of lightweight result dicts, e.g. {"title": str, "url": str, "snippet": str}.

    Raises:
        ToolError: if no provider is configured.
    """
    # Placeholder implementation: raise with a helpful message.
    raise ToolError(
        "web_search is not configured. Provide a provider-backed implementation "
        "(e.g., DuckDuckGo, SerpAPI) or mock in tests."
    )


_ALLOWED_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
}


def _sandbox_globals(capture: io.StringIO | None = None) -> dict[str, Any]:
    g: dict[str, Any] = {
        "__builtins__": _ALLOWED_BUILTINS | ({"print": (lambda *a, **k: None)} if capture else {}),
        "math": math,
    }
    if capture is not None:
        def _p(*args: Any, **kwargs: Any) -> None:  # simple print replacement
            sep = kwargs.get("sep", " ")
            end = kwargs.get("end", "\n")
            capture.write(sep.join(str(a) for a in args) + end)
        g["print"] = _p
    return g


@tool
def py_eval(expr: str) -> str:
    """Evaluate a simple Python expression in a minimal sandbox.

    Allowed: math and basic builtins (abs, min, max, sum, len, range, enumerate, zip).
    Disallowed: imports, attribute access that relies on __import__, I/O, etc.

    Returns the stringified result.
    """
    if not expr.strip():
        raise ToolError("expr must be non-empty")
    # Reject obvious dangerous tokens
    if re.search(r"__|import|open|exec|eval|os\.|sys\.", expr):
        raise ToolError("disallowed tokens in expression")
    try:
        result = eval(expr, _sandbox_globals(), {})
    except Exception as e:
        raise ToolError(str(e)) from e
    return str(result)


@tool
def py_exec(code: str) -> str:
    """Execute simple Python code in a minimal sandbox and capture stdout.

    - Provides a restricted set of builtins and the math module.
    - No imports available (no __import__).
    - Output is what `print(...)` writes.
    """
    if not code.strip():
        raise ToolError("code must be non-empty")
    if re.search(r"__|import|open|exec\(|eval\(|os\.|sys\.", code):
        raise ToolError("disallowed tokens in code")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, _sandbox_globals(capture=buf), {})
    except Exception as e:
        raise ToolError(str(e)) from e
    return buf.getvalue()

