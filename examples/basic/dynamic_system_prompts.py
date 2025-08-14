"""
Alloy equivalent: dynamic system instructions via per-call overrides.

Run:
  python examples/basic/dynamic_system_prompts.py

Notes:
- Use ask(..., system=...) to set instructions dynamically per call.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from alloy import ask


def dynamic_instructions(ctx: Any) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    user_name = getattr(ctx, "context", {}).get("name", "User")
    return (
        f"You are a precise assistant. Today's date is {now}. "
        f"The user's name is {user_name}. Respond concisely and cite steps clearly."
    )


def main() -> None:
    load_dotenv()
    ctx = {"name": "Alice"}
    system = dynamic_instructions({"context": ctx})
    out = ask("Help me plan a 30‑minute push workout.", context={"name": "Alice"}, system=system)
    print(out)


if __name__ == "__main__":
    main()
