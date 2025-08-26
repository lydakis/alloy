"""
Deep research (minimal plan + execute)

Run:
  python examples/90-advanced/02_deep_research.py

Notes:
- Planner + executor pattern; writes intermediate artifacts to a workspace
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

from pathlib import Path
from alloy import command, configure
from dotenv import load_dotenv


WORKSPACE = Path(__file__).with_name("_workspace_deep_research")


@command
def plan(goal: str) -> str:
    return f"Break the goal into 4–6 concrete steps (one per line): {goal}"


@command
def execute_step(goal: str, step: str, context: str) -> str:
    return f"Given the goal '{goal}', execute the step: {step}. Context so far:\n{context}"


def deep_agent(goal: str) -> str:
    WORKSPACE.mkdir(exist_ok=True)
    steps = [s.strip("- • ") for s in plan(goal).splitlines() if s.strip()]
    context: list[str] = []
    for i, step in enumerate(steps[:6], start=1):
        out = execute_step(goal, step, "\n".join(context[-3:]))
        (WORKSPACE / f"step_{i:02d}.txt").write_text(out)
        context.append(out)
    summary = ("\n\n").join(context[-3:])
    (WORKSPACE / "summary.txt").write_text(summary)
    return summary


def main():
    load_dotenv()
    configure(temperature=0.2)
    print(deep_agent("Survey approaches to evaluate AI-generated functions."))


if __name__ == "__main__":
    main()
