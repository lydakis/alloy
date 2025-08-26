"""
Simple evaluation (exact match)

Run:
  python examples/90-advanced/05_eval_simple.py

Notes:
  - Tiny eval harness: ask → compare → accuracy
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from alloy import command, configure
from dotenv import load_dotenv


@command
def answer_short(question: str) -> str:
    return f"Answer briefly and precisely: {question}"


@dataclass
class Example:
    q: str
    a: str


def run_eval(examples: Iterable[Example]) -> float:
    correct = 0
    total = 0
    for ex in examples:
        pred = answer_short(ex.q).strip()
        total += 1
        if pred.lower() == ex.a.strip().lower():
            correct += 1
        print(f"Q: {ex.q}\nP: {pred}\nG: {ex.a}\n")
    return (correct / total) if total else 0.0


def main():
    load_dotenv()
    configure(temperature=0.0)
    data = [
        Example("2+2?", "4"),
        Example("Opposite of 'cold'?", "hot"),
    ]
    acc = run_eval(data)
    print(f"Accuracy: {acc:.0%}")


if __name__ == "__main__":
    main()
