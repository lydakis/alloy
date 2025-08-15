# Tool Recipes (Minimal)

Alloy emphasizes small, composable primitives. You can wire any capability as a
`@tool` using the libraries you already trust. Below are minimal, copy‑pasteable
examples you can drop into your project.

## HTTP fetch (GET)

```python
from __future__ import annotations

import urllib.request
import urllib.parse
from typing import Any
from alloy import tool

@tool
def http_fetch(url: str, *, timeout_s: float = 8.0, max_bytes: int = 200_000) -> str:
    """Fetch a URL over http/https and return text (best‑effort decode).

    Minimal design: stdlib only, timeouts, byte cap, scheme allowlist.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("only http/https allowed")
    req = urllib.request.Request(url, headers={"User-Agent": "alloy-tool/1"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec B310
        data = resp.read(max_bytes)
        try:
            return data.decode("utf-8", errors="replace")
        except Exception:
            return data.decode("latin-1", errors="replace")
```

## Local file search

```python
from __future__ import annotations

import os, glob
from alloy import tool

@tool
def file_search(query: str, *, paths: list[str], max_files: int = 5, max_chars: int = 240) -> list[dict]:
    """Search local text files (simple substring match) and return [{path, snippet}]."""
    if not query.strip() or not paths:
        raise ValueError("query and paths are required")
    patterns: list[str] = []
    for p in paths:
        patterns.append(os.path.join(p, "**", "*") if os.path.isdir(p) else p)
    hits: list[dict] = []
    needle = query.lower()
    seen: set[str] = set()
    for pat in patterns:
        for fp in glob.iglob(pat, recursive=True):
            if len(hits) >= max_files or fp in seen or not os.path.isfile(fp):
                continue
            seen.add(fp)
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
                    hits.append({"path": fp, "snippet": data[start:end].strip()})
    return hits
```

## Python execution (dev‑only; dangerous)

These are for sandboxed demos only. Do not enable in production. You can gate
them behind an env var like `ALLOY_ENABLE_PY_EXEC=1`.

```python
from __future__ import annotations

import io, re, math, os, contextlib
from typing import Any
from alloy import tool

ALLOY_ENABLE_PY_EXEC = os.getenv("ALLOY_ENABLE_PY_EXEC") == "1"

def _sandbox_globals(capture: io.StringIO | None = None) -> dict[str, Any]:
    allowed = {
        "__builtins__": {"abs": abs, "min": min, "max": max, "sum": sum, "len": len, "range": range},
        "math": math,
    }
    if capture is not None:
        def _p(*args: Any, **kwargs: Any) -> None:
            sep = kwargs.get("sep", " ")
            end = kwargs.get("end", "\n")
            capture.write(sep.join(str(a) for a in args) + end)
        allowed["print"] = _p
    return allowed

@tool
def py_eval_dev(expr: str) -> str:
    if not ALLOY_ENABLE_PY_EXEC:
        raise PermissionError("py_eval_dev disabled; set ALLOY_ENABLE_PY_EXEC=1 to enable")
    if re.search(r"__|import|open|exec|eval|os\.|sys\.", expr):
        raise ValueError("disallowed tokens in expr")
    return str(eval(expr, _sandbox_globals(), {}))

@tool
def py_exec_dev(code: str) -> str:
    if not ALLOY_ENABLE_PY_EXEC:
        raise PermissionError("py_exec_dev disabled; set ALLOY_ENABLE_PY_EXEC=1 to enable")
    if re.search(r"__|import|open|exec\(|eval\(|os\.|sys\.", code):
        raise ValueError("disallowed tokens in code")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(code, _sandbox_globals(capture=buf), {})
    return buf.getvalue()
```

Guidance
- Keep tools tiny; add deps only when you must.
- Validate inputs and cap work (timeouts, byte limits).
- Prefer returning compact, easy‑to‑parse shapes from tools.
- If a tool grows complex, consider isolating it as a separate package.

## Provider‑backed web search (optional)

Option A: SerpAPI (requires `requests` and `SERPAPI_KEY`)

```python
from __future__ import annotations

import os, requests
from alloy import tool

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

@tool
def web_search_serpapi(query: str, *, max_results: int = 3) -> list[dict]:
    if not SERPAPI_KEY:
        raise RuntimeError("Set SERPAPI_KEY to enable web_search_serpapi")
    r = requests.get(
        "https://serpapi.com/search",
        params={"q": query, "engine": "google", "api_key": SERPAPI_KEY},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    items = []
    for item in (data.get("organic_results") or [])[:max_results]:
        items.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return items
```

Option B: DuckDuckGo (requires `duckduckgo_search`)

```python
from __future__ import annotations

from duckduckgo_search import DDGS
from alloy import tool

@tool
def web_search_ddg(query: str, *, max_results: int = 3) -> list[dict]:
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results) or []
    return [{"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")} for r in results]
```
