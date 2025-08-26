"""
Pytest test generator

Run:
  python examples/60-integration/04_pytest_generator.py

Notes:
  - Generates a minimal pytest file from a description
  - Prints to stdout; redirect to a file if desired
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command
def generate_tests(description: str, module_name: str) -> str:
    return f"""
    Write a small pytest test module to validate this module: {module_name}
    Use 2–3 tests that focus on edge cases described here:
    {description}

    Return only the test code (no backticks).
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    spec = (
        "The module exposes add(a,b) and div(a,b).\n"
        "Edge cases: div by zero, negative numbers, large ints."
    )
    print(generate_tests(spec, "my_math"))


if __name__ == "__main__":
    main()

