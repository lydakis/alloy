"""
Conversation history manager (stateless Alloy, stateful wrapper)

Run:
  python examples/80-patterns/07_conversation_history.py

Notes:
  - Manages a rolling transcript across turns per session_id
  - Passes last N turns as context into a command reply
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from alloy import command, configure
from dotenv import load_dotenv

ROOT = Path(__file__).with_name("_conversations")
ROOT.mkdir(exist_ok=True)


def _path(session_id: str) -> Path:
    return ROOT / f"{session_id}.json"


def _load(session_id: str) -> list[dict]:
    p = _path(session_id)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(session_id: str, items: list[dict]) -> None:
    _path(session_id).write_text(json.dumps(items, ensure_ascii=False, indent=2))


class ConversationStore:
    def append(self, session_id: str, role: Literal["user", "assistant"], text: str) -> None:
        items = _load(session_id)
        items.append({"role": role, "text": str(text)})
        _save(session_id, items)

    def transcript(self, session_id: str, last: int = 8) -> str:
        items = _load(session_id)
        # Use only the most recent turns
        recent = items[-int(last) :] if last > 0 else items
        lines: list[str] = []
        for it in recent:
            r = it.get("role", "")
            t = it.get("text", "")
            if r and t:
                lines.append(f"{r.capitalize()}: {t}")
        return "\n".join(lines)


@command(output=str)
def chat_reply(message: str, transcript: str) -> str:
    return f"""
    You are a helpful assistant. Continue the conversation.

    Context (recent turns):
    {transcript}

    User: {message}
    Respond succinctly and helpfully, keeping style consistent with prior turns.
    """


def demo_conversation():
    store = ConversationStore()
    sid = "demo"
    # Turn 1
    user1 = "Hello, I'm Sam — no emojis please."
    print("User:", user1)
    r1 = chat_reply(user1, store.transcript(sid, last=6))
    print("Assistant:", r1)
    store.append(sid, "user", user1)
    store.append(sid, "assistant", r1)
    # Turn 2
    user2 = "What did I say about emojis?"
    print("User:", user2)
    r2 = chat_reply(user2, store.transcript(sid, last=6))
    print("Assistant:", r2)
    store.append(sid, "user", user2)
    store.append(sid, "assistant", r2)


def main():
    load_dotenv()
    configure(temperature=0.2)
    demo_conversation()


if __name__ == "__main__":
    main()
