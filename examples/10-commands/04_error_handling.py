"""
Error handling with CommandError

Run:
  python examples/10-commands/04_error_handling.py

Offline:
  ALLOY_BACKEND=fake python examples/10-commands/04_error_handling.py
"""

from alloy import command, CommandError


@command(output=float)
def extract_price(text: str) -> str:
    return f"Extract price from: {text}"


def main():
    try:
        price = extract_price("No price here")
        print("Price:", price)
    except CommandError as e:
        print(f"Extraction failed: {e}")


if __name__ == "__main__":
    main()

