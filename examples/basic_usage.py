from dataclasses import dataclass
import os, sys

# Ensure project root (with `alloy/`) is importable when running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from alloy import command, tool, ask, configure


def main():
    # Load environment variables (e.g., OPENAI_API_KEY)
    load_dotenv()

    # Configure OpenAI with the desired model
    # Ensure OPENAI_API_KEY is set in your environment
    # Some models may not support temperature; omit unless needed
    configure(model="gpt-5")

    @command(output=float)
    def ExtractPrice(text: str) -> str:
        """Extract price from text."""
        return f"Extract the price (number only) from: {text}"

    price = ExtractPrice("This item costs $49.99 with free shipping.")
    print("Price:", price)

    # Ask without structure
    print(ask("Explain quantum computing in one sentence."))


if __name__ == "__main__":
    main()
