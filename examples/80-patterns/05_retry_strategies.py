"""
Retry strategies

Run:
  python examples/80-patterns/05_retry_strategies.py

Notes:
  - Demonstrates per-command retry on failure
  - Use retry to re-run the whole command; max_tool_turns bounds tool loops
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command(retry=2)
def fragile_task(input_text: str) -> str:
    return f"""
    Do this task robustly even if the first attempt fails:
    {input_text}
    If you previously failed to produce an answer, try a simpler approach now.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)
    print(fragile_task("Summarize: A terse, technical overview of Alloy."))


if __name__ == "__main__":
    main()
