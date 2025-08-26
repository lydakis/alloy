"""
List outputs (list[dataclass])

Run:
  python examples/20-typed/03_list_output.py

Notes:
  - Demonstrates returning a list of structured items
  - Offline: export ALLOY_BACKEND=fake
"""

from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv


@dataclass
class Task:
    action: str
    owner: str
    priority: str


@command(output=list[Task])
def plan_tasks(goal: str, team: list[str]) -> str:
    """Produce a short prioritized plan as a list of tasks."""
    return f"""
    Goal: {goal}
    Team: {team}

    Return a concise list of 3–5 tasks with action, owner, and priority.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    tasks = plan_tasks("Ship a minimal landing page", ["Alice", "Bob", "Chen"])
    for t in tasks:
        print(f"[{t.priority}] {t.owner}: {t.action}")


if __name__ == "__main__":
    main()
