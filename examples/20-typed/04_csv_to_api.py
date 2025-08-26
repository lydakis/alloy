"""
Real-world CSV to API payload mapper

Run:
  python examples/20-typed/04_csv_to_api.py

Requirements:
  - pandas (see examples/requirements.txt)

Notes:
  - Shows typed list output for practical data transformation
  - Offline: export ALLOY_BACKEND=fake
"""

from dataclasses import dataclass, asdict
from alloy import command, configure
import pandas as pd
import json
from dotenv import load_dotenv


@dataclass
class CustomerPayload:
    fullName: str
    emailAddress: str
    subscriptionTier: str


@command(output=list[CustomerPayload])
def csv_to_api(df: pd.DataFrame, endpoint_spec: str) -> str:
    return f"""
    Map CSV data to match this API endpoint: {endpoint_spec}

    CSV columns: {df.columns.tolist()}
    Sample rows: {df.head(3).to_dict('records')}

    Return a JSON array of objects matching the required format.
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    # Sample messy CSV data
    df = pd.DataFrame(
        {
            "First Name": ["John", "Jane"],
            "Last Name": ["Doe", "Smith"],
            "Email Address": ["john@example.com", "jane@example.com"],
            "Plan": ["Pro", "Enterprise"],
        }
    )

    # Map to API format
    payloads = csv_to_api(df, "POST /customers {fullName, emailAddress, subscriptionTier}")

    for payload in payloads:
        print("Ready to POST:")
        print(json.dumps(asdict(payload), indent=2))
        # requests.post("https://api.example.com/customers", json=asdict(payload))


if __name__ == "__main__":
    main()
