"""
Payment pipeline with contracts

Run:
  python examples/40-contracts/04_payment_pipeline.py

Notes:
  - Enforces validate → charge → receipt via @require/@ensure
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

from dataclasses import dataclass
from alloy import tool, command, require, ensure, configure
from dotenv import load_dotenv


@tool
@ensure(lambda p: p.get("is_valid", False) is True, "validation must set is_valid=True")
def validate_payment(payment: dict) -> dict:
    """Basic validation (mock); marks payment as valid."""
    p = dict(payment)
    p["is_valid"] = bool(p.get("amount", 0) > 0 and p.get("card_last4"))
    return p


@tool
@require(
    lambda ba: ba.arguments.get("payment", {}).get("is_valid") is True, "run validate_payment first"
)
@ensure(lambda res: res is True, "charge must succeed")
def charge_card(payment: dict) -> bool:
    """Charge the card (mock)."""
    # pretend to call PSP and succeed
    return True


@tool
@ensure(lambda ok: ok is True, "receipt must be sent")
def send_receipt(email: str, amount: float) -> bool:
    """Send a receipt email (mock)."""
    print(f"Sent receipt to {email} for ${amount}")
    return True


@dataclass
class PaymentResult:
    status: str
    charged: bool
    receipt_sent: bool


@command(output=PaymentResult, tools=[validate_payment, charge_card, send_receipt])
def process_payment(payment: dict) -> str:
    return f"""
    Process a payment in order:
    1) validate_payment(payment) -> adds is_valid
    2) charge_card(payment)
    3) send_receipt(email, amount)

    Return PaymentResult with status, charged, and receipt_sent.

    Payment: {payment}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    payment = {"email": "bob@example.com", "amount": 49.99, "card_last4": "4242"}
    res = process_payment(payment)
    print(res)


if __name__ == "__main__":
    main()
