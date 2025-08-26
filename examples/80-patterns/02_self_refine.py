"""
Self-refine: iterative improvement loop

Run:
  python examples/80-patterns/02_self_refine.py

Notes:
  - Python controls the loop; commands generate and critique
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command
def draft_solution(task: str) -> str:
    return f"Draft a concise solution to: {task}"


@command
def critique_and_suggest(task: str, draft: str) -> str:
    return f"Critique this draft for '{task}' and suggest concrete improvements:\n{draft}"


@command
def apply_suggestions(draft: str, suggestions: str) -> str:
    return f"Apply these improvements to the draft:\n{draft}\n\nImprovements:\n{suggestions}"


def self_refine(task: str, rounds: int = 2) -> str:
    text = draft_solution(task)
    for _ in range(max(0, rounds)):
        feedback = critique_and_suggest(task, text)
        text = apply_suggestions(text, feedback)
    return text


def main():
    load_dotenv()
    configure(temperature=0.2)
    print(self_refine("Write a helpful README blurb for Alloy."))


if __name__ == "__main__":
    main()

