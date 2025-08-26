"""
Triage pattern - route to specialized commands

Run:
  python examples/50-composition/02_routing_triage.py

Notes:
  - Commands compose without orchestration frameworks
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import command, configure
from dotenv import load_dotenv


@command(output=str)
def triage(message: str) -> str:
    return f"""
    Classify this customer message into exactly one category:
    - billing (payment issues, charges, refunds)
    - technical (bugs, errors, not working)
    - general (questions, feedback, other)

    Message: {message}
    Return only the category word.
    """


@command(output=str)
def handle_billing(message: str) -> str:
    return f"""
    As a billing specialist, resolve this issue:
    {message}

    Provide specific next steps and any required information.
    """


@command(output=str)
def handle_technical(message: str) -> str:
    return f"""
    As a technical support engineer, diagnose this issue:
    {message}

    Provide troubleshooting steps or escalation path.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    message = "I was charged twice for my subscription last month"

    # Route to specialist
    category = triage(message).strip().lower()
    print(f"Routed to: {category}")

    if category == "billing":
        response = handle_billing(message)
    elif category == "technical":
        response = handle_technical(message)
    else:
        response = "I'll connect you with a human agent."

    print(f"Response: {response}")


if __name__ == "__main__":
    main()

