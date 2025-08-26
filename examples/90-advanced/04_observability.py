"""
Observability: timing and logging wrapper

Run:
  python examples/90-advanced/04_observability.py

Notes:
  - Wrap commands to time execution and print durations
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

import time
from functools import wraps
from alloy import command, configure
from dotenv import load_dotenv


def timed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            dt = (time.perf_counter() - t0) * 1000
            print(f"{fn.__name__} took {dt:.1f} ms")

    return wrapper


@command
def generate(user_request: str) -> str:
    return f"Generate a concise response for: {user_request}"


@timed
def generate_timed(user_request: str) -> str:
    return generate(user_request)


def main():
    load_dotenv()
    configure(temperature=0.2)
    print(generate_timed("Observability patterns for Alloy commands"))


if __name__ == "__main__":
    main()
