# Tutorial (10 Minutes)

Audience: developers new to Alloy who want a fast first run.
Outcome: run ask(), write a command, add a type, call a tool, use a contract, stream text, and switch providers.
Time: ~10 minutes
Prereqs: Python 3.10+. `pip install alloy-ai` (or `pip install 'alloy-ai[providers]'`). Set a provider key, or use `ALLOY_BACKEND=fake` for offline.

!!! success "Outcomes first"
    By the end you’ll have:

    - A working `ask()`
    - Your first `@command`
    - One typed output
    - One safe tool
    - A small workflow guarded by contracts

---

## 1) Explore with `ask()`

What you’ll learn: freeform Q&A for quick exploration.

Code (tutorial_step1.py)
```python
from alloy import ask

print(ask("Say hello!"))
```

Run
```bash
python tutorial_step1.py
```

You'll see: a short greeting.

---

## 2) First `@command` (text)

What you’ll learn: the function returns a prompt string; the decorator runs the model.

Code (tutorial_step2.py)
```python
from alloy import command

@command  # returns str by default
def summarize(text: str) -> str:
    return f"Summarize in one sentence: {text}"

print(summarize("Alloy lets you write typed AI functions in Python."))
```

Run: `python tutorial_step2.py`

You'll see: a one‑sentence summary.

---

## 3) Enforce a type (dataclass)

What you’ll learn: provider‑enforced typed output; clear errors if shape is wrong.

Code (tutorial_step3.py)
```python
from dataclasses import dataclass
from alloy import command

@dataclass
class ArticleSummary:
    title: str
    key_points: list[str]
    reading_time_minutes: int

@command(output=ArticleSummary)
def summarize_article(text: str) -> str:
    return f"""
    Summarize with: title, 3–5 key_points, reading_time_minutes.
    Article: {text}
    """

res = summarize_article("Python emphasizes readability and has a vast ecosystem.")
print(res.title)
```

Run: `python tutorial_step3.py`

You'll see: a structured object; IDE autocompletes fields.

---

## 4) Add a tool (plain Python)

What you’ll learn: give the model a small local capability.

Code (tutorial_step4.py)
```python
from alloy import command, tool

@tool
def word_count(text: str) -> int:
    return len(text.split())

@command(tools=[word_count])
def analyze(text: str) -> str:
    return f"Use word_count(text), then suggest one clarity improvement.\nText: {text}"

print(analyze("Alloy makes typed AI functions feel like normal Python."))
```

Run: `python tutorial_step4.py`

You'll see: a short analysis referencing the word count.

---

## 5) Add a contract (DBC: require/ensure)

What you’ll learn: enforce order/invariants with fast, actionable feedback.

Code (tutorial_step5.py)
```python
import datetime
from alloy import command, tool, require, ensure

@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "Must add validated_at")
def validate_data(data: dict) -> dict:
    d = dict(data)
    d["validated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return d

@tool
@require(lambda ba: "validated_at" in ba.arguments.get("data", {}), "Run validate_data first")
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    return True

@command(output=str, tools=[validate_data, save_to_production])
def process_order(order: dict) -> str:
    return f"Validate then save this order: {order}"

print(process_order({"id": 123, "amount": 99.99}))
```

Run: `python tutorial_step5.py`

You'll see: a short message indicating the steps; contracts guide the model.

---

## 6) Streaming (text‑only today)

What you’ll learn: stream text chunks; typed outputs/tools don’t stream.

Code (tutorial_step6.py)
```python
from alloy import ask, command

@command
def brainstorm(topic: str) -> str:
    return f"Write a short riff about: {topic}"

for chunk in ask.stream("Write a one-liner about cats"):
    print(chunk, end="")
print()

for chunk in brainstorm.stream("Alloy examples"):
    print(chunk, end="")
print()
```

Run: `python tutorial_step6.py`

You'll see: streamed text printed inline for both loops (two short lines).

Note: Commands with tools or typed outputs don’t stream. Details: [Guide → Streaming](../guide/streaming.md).

---

## 7) Switch providers (no code changes)

What you’ll learn: portability — same code, different models.

Run one of the following (pick a provider you’ve configured):
```bash
export OPENAI_API_KEY=...;   ALLOY_MODEL=gpt-5-mini            python tutorial_step3.py
export ANTHROPIC_API_KEY=...; ALLOY_MODEL=claude-sonnet-4-20250514 python tutorial_step3.py
export GOOGLE_API_KEY=...;    ALLOY_MODEL=gemini-2.5-flash      python tutorial_step3.py
ALLOY_MODEL=ollama:<model>    python tutorial_step3.py
```

Expected: the same structured result across providers (style may vary).

---

Next steps
- [Examples (curated)](../examples/index.md)
- [Providers (capability matrix + setup)](../guide/providers.md)
- [Configuration (precedence and overrides)](../guide/configuration.md)
 - [Common Pitfalls](../guide/pitfalls.md)
