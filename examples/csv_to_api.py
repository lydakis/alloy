from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

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
        "Return only a JSON array of request payloads, one per row.\n"
        f"Columns: {columns}\nSample rows: {head}\n"
        f"Endpoint example: {endpoint_example}"
    )


def main():
    # Demo CSV
    data = {
        "Customer Name": ["Ada Lovelace", "Linus Torvalds"],
        "Email": ["ada@example.com", "linus@example.com"],
        "Plan Type": ["pro", "enterprise"],
    }
    df = pd.DataFrame(data)

    payloads = CSVToAPI(df, "POST /customers {fullName, emailAddress, subscriptionTier}")
    print("Generated", len(payloads), "payloads:")
    for p in payloads:
        print(p)


if __name__ == "__main__":
    main()

