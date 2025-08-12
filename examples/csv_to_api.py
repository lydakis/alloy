from __future__ import annotations

import json
import pandas as pd
from dotenv import load_dotenv

from alloy import command


@command(output=list[dict])
def CSVToAPI(df: pd.DataFrame, endpoint_example: str) -> str:
    """Intelligently map CSV columns to API format.

    The model inspects the dataframe shape and a short endpoint example and
    returns a list of request payloads ready for POSTing.
    """
    # Provide a compact summary to keep tokens low
    head = df.head(5).to_dict(orient="records")
    columns = df.columns.tolist()
    return (
        "Map the CSV rows to match the target API request schema. "
        "Return only a compact JSON array of objects (no comments, fences, or extra text).\n"
        f"Columns: {columns}\nSample rows: {head}\n"
        f"Endpoint example: {endpoint_example}"
    )


def main():
    # Load provider API keys from .env (e.g., OPENAI_API_KEY)
    load_dotenv()
    # Tip: run offline with `ALLOY_BACKEND=fake` for a quick demo
    # Or set `configure(model="gpt-5-mini")` for explicit default
    # Demo CSV
    data = {
        "Customer Name": ["Ada Lovelace", "Linus Torvalds"],
        "Email": ["ada@example.com", "linus@example.com"],
        "Plan Type": ["pro", "enterprise"],
    }
    df = pd.DataFrame(data)

    payloads = CSVToAPI(df, "POST /customers {fullName, emailAddress, subscriptionTier}")
    print("Generated", len(payloads), "payloads:")
    for p in payloads[:10]:  # print first 10 for brevity
        print(json.dumps(p, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
