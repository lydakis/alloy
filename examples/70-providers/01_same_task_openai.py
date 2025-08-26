"""
Invoice extraction with OpenAI

Run:
  python examples/70-providers/01_same_task_openai.py

Notes:
  - Set: export OPENAI_API_KEY=...
  - Uses: ALLOY_MODEL (or configure) to select model
  - Offline: export ALLOY_BACKEND=fake
"""

from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv


@dataclass
class Invoice:
    invoice_number: str
    date: str
    total_amount: float
    vendor_name: str


@command(output=Invoice)
def extract_invoice(text: str) -> str:
    return f"Extract invoice details from:\n{text}"


def main():
    load_dotenv()
    configure(model="gpt-5-mini", temperature=0.1)

    invoice_text = """
    INVOICE #INV-2024-001
    Date: March 15, 2024

    Bill To: Acme Corp
    From: Widgets Inc

    Items:
    - Widget A: $49.99
    - Widget B: $75.00

    Total: $124.99
    """

    result = extract_invoice(invoice_text)
    print(f"Invoice: {result.invoice_number}")
    print(f"Total: ${result.total_amount}")


if __name__ == "__main__":
    main()

