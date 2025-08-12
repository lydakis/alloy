import os

from dotenv import load_dotenv
from alloy import command, ask


def main():
    # Load environment variables (e.g., OPENAI_API_KEY)
    load_dotenv()

    # Configure OpenAI (optional): default model is `gpt-5-mini` if omitted
    # Ensure OPENAI_API_KEY is set in your environment
    # Tip: cap tool iterations globally via `export ALLOY_MAX_TOOL_TURNS=1`
    # configure(model="gpt-5-mini")

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
