"""
The simplest possible Alloy usage - just ask a question

Run:
  python examples/00-explore/00_hello.py

Offline:
  ALLOY_BACKEND=fake python examples/00-explore/00_hello.py
"""

from alloy import ask


def main():
    print(ask("Say hello!"))


if __name__ == "__main__":
    main()
