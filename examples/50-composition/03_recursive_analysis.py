"""
Recursive analysis pattern

Run:
  python examples/50-composition/03_recursive_analysis.py

Notes:
  - A coordinating Python function uses multiple commands iteratively
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command
def propose_subtasks(goal: str) -> str:
    return f"Break the goal into 3–5 concrete subtasks (one per line): {goal}"


@command
def analyze_subtask(goal: str, subtask: str) -> str:
    return f"Given the goal '{goal}', analyze the subtask: {subtask}. Provide 2–3 crisp findings."


@command
def synthesize_report(goal: str, findings: str) -> str:
    return f"Synthesize a short report for '{goal}' from these findings:\n{findings}"


def recursive_analysis(goal: str, depth: int = 1) -> str:
    todo = [goal]
    findings: list[str] = []
    for _ in range(max(depth, 1)):
        new_todo: list[str] = []
        for g in todo:
            subtasks = [s.strip("- • ") for s in propose_subtasks(g).splitlines() if s.strip()]
            for st in subtasks[:4]:
                findings.append(analyze_subtask(g, st))
                # Could push deeper subtasks here if desired
        todo = new_todo
    return synthesize_report(goal, "\n".join(findings))


def main():
    load_dotenv()
    configure(temperature=0.2)
    print(recursive_analysis("Evaluate adding typed AI functions to our product", depth=1))


if __name__ == "__main__":
    main()

