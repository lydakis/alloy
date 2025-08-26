"""
Self-correcting tools via DBC failures

Run:
  python examples/40-contracts/03_self_correcting.py

Notes:
  - When a tool @require fails, the model sees a short error message
  - The model can adjust inputs on a subsequent call
  - Offline: export ALLOY_BACKEND=fake
"""

from alloy import tool, command, require, ensure, configure
from dotenv import load_dotenv


@tool
@require(lambda ba: isinstance(ba.arguments.get("email", ""), str) and ba.arguments.get("email", "").count("@") == 1,
         "provide a single valid email")
def extract_domain(email: str) -> str:
    """Return the domain part of an email address."""
    return email.split("@", 1)[1].lower()


@tool
@ensure(lambda s: isinstance(s, str) and s.isupper(), "must return uppercase text")
def shout(text: str) -> str:
    """Uppercase the text and ensure it is uppercase."""
    return str(text).upper()


@command(tools=[extract_domain, shout])
def clean_and_report(raw_text: str) -> str:
    return f"""
    From the raw text, find an email address. If your first attempt fails,
    correct the input and try once more (at most two attempts), then:
    - Call extract_domain(email) to get the domain
    - Call shout(domain) to produce an uppercase label
    Return: "DOMAIN: <UPPERCASE_DOMAIN>" and one sentence about your fixups.

    Raw text: {raw_text}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    messy = "Contact us at support[at]example.com or visit our site."
    print(clean_and_report(messy))


if __name__ == "__main__":
    main()
