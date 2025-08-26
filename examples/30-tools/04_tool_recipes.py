"""
Tool recipes: HTTP, file, and SQL

Run:
  python examples/30-tools/04_tool_recipes.py

Notes:
  - Uses stdlib: urllib (HTTP), pathlib (file), sqlite3 (SQL)
  - Network required for HTTP fetch; skip if offline
  - Offline: export ALLOY_BACKEND=fake (tools still run locally)
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.request import urlopen

from alloy import tool, command, configure
from dotenv import load_dotenv


@tool
def http_get_json(url: str, timeout: float = 5.0) -> dict:
    """Fetch JSON from a URL (GET)."""
    with urlopen(url, timeout=timeout) as resp:  # nosec - example only
        data = resp.read().decode("utf-8")
    return json.loads(data)


@tool
def read_text_file(path: str, max_chars: int = 500) -> str:
    """Read up to max_chars from a local text file."""
    p = Path(path)
    if not p.exists():
        return ""
    content = p.read_text(encoding="utf-8", errors="ignore")
    return content[: int(max_chars)]


@tool
def sql_query(query: str) -> list[dict]:
    """Run a SQL query on an in-memory demo DB and return rows."""
    con = sqlite3.connect(":memory:")
    try:
        cur = con.cursor()
        cur.execute("create table if not exists people(id int, name text)")
        cur.executemany(
            "insert into people(id,name) values(?,?)",
            [(1, "Ada"), (2, "Linus"), (3, "Guido")],
        )
        cur.execute(query)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows
    finally:
        con.close()


@command(tools=[http_get_json, read_text_file, sql_query])
def demo_recipes(tmp_file: str) -> str:
    return """
    Use the tools to:
    1) Read a local file snippet using read_text_file(tmp_file)
    2) Query an in-memory DB: select name from people where id in (1,3)
    3) Optionally fetch JSON from https://httpbin.org/json (if network available)

    Provide a compact summary of results.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    # Prepare a small file
    sample_path = Path(__file__).with_name("_sample.txt")
    sample_path.write_text("Alloy integrates AI into normal Python.\n", encoding="utf-8")

    result = demo_recipes(str(sample_path))
    print(result)


if __name__ == "__main__":
    main()
