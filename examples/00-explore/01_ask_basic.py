"""
Simplest Alloy usage - exploratory ask()

Run:
  python examples/00-explore/01_ask_basic.py

Notes:
  - No structure needed for exploration
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import ask, configure
from dotenv import load_dotenv


def main():
    load_dotenv()
    configure(temperature=0.2)

    # Exploration without commands
    answer = ask("What are the main components of a REST API?")
    print(answer)

    # Another simple query without extra structure
    tip = ask("Give one practical tip for writing clean Python.")
    print(tip)


if __name__ == "__main__":
    main()
