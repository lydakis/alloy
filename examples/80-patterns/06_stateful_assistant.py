"""
Stateful assistant via file-backed memory (facts + summary)

Run:
  python examples/80-patterns/06_stateful_assistant.py

Purpose:
  - Show long-term memory managed in Python (files), not inside Alloy

Notes:
  - Alloy stays stateless; tools load/save/recall facts
  - Keep it simple: no fancy policies, just demonstrate the pattern
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

import json
import datetime as dt
from pathlib import Path
from dataclasses import dataclass
from alloy import command, tool, configure
from dotenv import load_dotenv


ROOT = Path(__file__).with_name("_memory_stateful")
ROOT.mkdir(exist_ok=True)


def _path(user_id: str) -> Path:
    return ROOT / f"{user_id}.json"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


@tool
def load_profile(user_id: str) -> dict:
    """Load user profile memory {facts: [..], summary: str}."""
    p = _path(user_id)
    if not p.exists():
        return {"facts": [], "summary": "", "updated_at": _now()}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"facts": [], "summary": "", "updated_at": _now()}


@tool
def save_profile(user_id: str, profile: dict) -> bool:
    """Persist profile back to disk."""
    p = _path(user_id)
    data = dict(profile)
    data["updated_at"] = _now()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return True


@tool
def remember(user_id: str, fact: str) -> bool:
    """Append a durable fact if new."""
    prof = load_profile(user_id)
    facts = list(prof.get("facts", []))
    if fact and fact not in facts:
        facts.append(fact)
        prof["facts"] = facts
        save_profile(user_id, prof)
    return True


@tool
def recall(user_id: str, query: str, k: int = 5) -> list[str]:
    """Naive keyword recall of relevant facts (top-k)."""
    prof = load_profile(user_id)
    q = str(query).lower()
    facts = [f for f in prof.get("facts", []) if any(w and w in f.lower() for w in q.split())]
    return facts[: int(k)]


@dataclass
class AssistantTurn:
    reply: str
    new_facts: list[str]


# Minimal system prompt to keep example focused
ASSISTANT_SYSTEM = "Be concise. Use the memory tools when helpful."


@command(
    output=AssistantTurn,
    tools=[load_profile, save_profile, recall, remember],
    system=ASSISTANT_SYSTEM,
)
def assistant_turn(user_id: str, message: str) -> str:
    return f"""
    Task:
    - Read profile and relevant facts; reply concisely.
    - If suitable, include up to two durable facts in new_facts and store them.

    Input:
    user_id={user_id}
    message={message}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)
    uid = "alice"
    msg1 = "Hi, I prefer emails in the morning."
    res1 = assistant_turn(uid, msg1)
    print("User:", msg1)
    print("Assistant:", res1.reply)
    if res1.new_facts:
        print("New facts:", res1.new_facts)

    msg2 = "Schedule a follow-up tomorrow."
    res2 = assistant_turn(uid, msg2)
    print("User:", msg2)
    print("Assistant:", res2.reply)
    if res2.new_facts:
        print("New facts:", res2.new_facts)


if __name__ == "__main__":
    main()
