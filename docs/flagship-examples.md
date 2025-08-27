# Flagship Examples

These are small, copy‑pasteable examples that demonstrate Alloy’s core patterns. Each snippet links to a runnable script under `examples/`.

Tip
- Install optional deps: `pip install -r examples/requirements.txt`
- Pick a model (e.g., `export ALLOY_MODEL=gpt-5-mini`) and set your provider key
- Offline mode: `export ALLOY_BACKEND=fake`

## Ask: exploratory

Path: `examples/00-explore/01_ask_basic.py`

When to use: quick exploration, ad‑hoc questions, ideation before adding structure.

```python
from alloy import ask
from dotenv import load_dotenv

def main():
    load_dotenv()
    answer = ask("What are the main components of a REST API?")
    print(answer)

if __name__ == "__main__":
    main()
```

## First command: text output

Path: `examples/10-commands/01_first_command.py`

When to use: you want a reusable function that returns text; lightweight helpers, prompts you call from normal Python.

```python
from alloy import command, configure
from dotenv import load_dotenv

@command  # default typed output is str
def summarize(text: str) -> str:
    return f"Summarize in exactly 3 bullets:\n\n{text}"

def main():
    load_dotenv()
    configure(temperature=0.2)
    print(summarize("REST APIs use HTTP methods, resources, and representations."))

if __name__ == "__main__":
    main()
```

## Typed output: dataclass

Path: `examples/20-typed/02_dataclass_output.py`

When to use: you need a structured result (provider‑enforced) without manual parsing; great for API payloads, forms, and summaries.

```python
from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv

@dataclass
class ArticleSummary:
    title: str
    key_points: list[str]
    reading_time_minutes: int

@command(output=ArticleSummary)
def summarize_article(text: str) -> str:
    return f"""
    Read the article and produce:
    - title: concise title
    - key_points: 3–5 short bullets
    - reading_time_minutes: integer estimate

    Article:
    {text}
    """

def main():
    load_dotenv()
    configure(temperature=0.2)
    res = summarize_article("Python emphasizes code readability…")
    print("Title:", res.title)

if __name__ == "__main__":
    main()
```

## Contracts: validate → save workflow

Path: `examples/40-contracts/02_workflow_contracts.py`

When to use: workflows with explicit preconditions and postconditions; enforce tool order (validate → save) and surface failures for self‑correction.

```python
from alloy import command, tool, require, ensure, configure
from dotenv import load_dotenv
import datetime

@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "Must add validated_at timestamp")
def validate_data(data: dict) -> dict:
    data = dict(data)
    data["validated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return data

@tool
@require(lambda ba: "validated_at" in ba.arguments.get("data", {}), "Run validate_data first")
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    print(f"Saving to production: {data}")
    return True

@command(output=str, tools=[validate_data, save_to_production])
def process_order(order: dict) -> str:
    return f"""
    Process this order through our workflow:
    1. Validate the data (adds timestamp)
    2. Save to production

    Order: {order}

    Return a summary of actions taken.
    """
```

## RAG: answer with citations

Path: `examples/80-patterns/01_rag_citations.py`

When to use: questions that must cite sources; domain Q&A, compliance, and documentation lookups where provenance matters.

```python
from dataclasses import dataclass
from alloy import command, tool, configure

DOCUMENTS = {
    "doc1": "Python was created by Guido van Rossum and released in 1991.",
    "doc2": "Python emphasizes code readability and uses indentation.",
    "doc3": "Python supports multiple programming paradigms.",
}

@tool
def search_documents(query: str, max_results: int = 3) -> list[dict]:
    results = []
    for doc_id, content in DOCUMENTS.items():
        if any(word.lower() in content.lower() for word in query.split()):
            results.append({"id": doc_id, "content": content})
    return results[: int(max_results)]

@dataclass
class AnswerWithCitations:
    answer: str
    citations: list[str]
    confidence: float

@command(output=AnswerWithCitations, tools=[search_documents])
def answer_with_sources(question: str) -> str:
    return f"""
    Answer this question using search_documents tool:
    {question}

    Include specific citations (document IDs) for each claim.
    Rate your confidence 0.0-1.0 based on source quality.
    """
```

Further
- See the full suite under `examples/` for composition, integrations, providers, patterns, and advanced flows (deep agents, OCR, observability, evals).

## Stateful assistant: file-backed memory

Path: `examples/80-patterns/06_stateful_assistant.py`

When to use: durable, per‑user memory across sessions (preferences, profile facts); keep Alloy stateless and store memory in Python.

```python
from __future__ import annotations
import json, datetime as dt
from pathlib import Path
from dataclasses import dataclass
from alloy import command, tool

ROOT = Path(__file__).with_name("_memory_stateful"); ROOT.mkdir(exist_ok=True)
def _path(uid: str) -> Path: return ROOT / f"{uid}.json"
def _now() -> str: return dt.datetime.now(dt.timezone.utc).isoformat()

@tool
def load_profile(user_id: str) -> dict:
    p = _path(user_id)
    if not p.exists(): return {"facts": [], "summary": "", "updated_at": _now()}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return {"facts": [], "summary": "", "updated_at": _now()}

@tool
def save_profile(user_id: str, profile: dict) -> bool:
    data = dict(profile); data["updated_at"] = _now(); _path(user_id).write_text(json.dumps(data))
    return True

@tool
def remember(user_id: str, fact: str) -> bool:
    prof = load_profile(user_id); facts = list(prof.get("facts", []))
    if fact and fact not in facts: facts.append(fact); prof["facts"] = facts; save_profile(user_id, prof)
    return True

@tool
def recall(user_id: str, query: str, k: int = 5) -> list[str]:
    prof = load_profile(user_id); q = query.lower()
    return [f for f in prof.get("facts", []) if any(w and w in f.lower() for w in q.split())][:k]

@dataclass
class AssistantTurn: reply: str; new_facts: list[str]

@command(output=AssistantTurn, tools=[load_profile, save_profile, recall, remember], system="Be concise.")
def assistant_turn(user_id: str, message: str) -> str:
    return f"""
    Read profile and relevant facts; reply concisely.
    If suitable, include up to two durable facts in new_facts and store them.
    user_id={user_id}
    message={message}
    """
```

## Conversation history: rolling transcript

Path: `examples/80-patterns/07_conversation_history.py`

When to use: short‑term conversational continuity within a session; feed the recent transcript into each turn to keep context.

```python
from __future__ import annotations
import json
from pathlib import Path
from alloy import command

ROOT = Path(__file__).with_name("_conversations"); ROOT.mkdir(exist_ok=True)
def _path(sid: str) -> Path: return ROOT / f"{sid}.json"
def _load(sid: str) -> list[dict]:
    p = _path(sid)
    try: return json.loads(p.read_text()) if p.exists() else []
    except Exception: return []
def _save(sid: str, items: list[dict]) -> None: _path(sid).write_text(json.dumps(items))

class ConversationStore:
    def append(self, sid: str, role: str, text: str):
        items = _load(sid); items.append({"role": role, "text": text}); _save(sid, items)
    def transcript(self, sid: str, last: int = 8) -> str:
        return "\n".join(f"{it['role'].capitalize()}: {it['text']}" for it in _load(sid)[-last:])

@command(output=str)
def chat_reply(message: str, transcript: str) -> str:
    return f"""
    Continue the conversation based on recent turns:\n{transcript}\n\nUser: {message}
    """
```
