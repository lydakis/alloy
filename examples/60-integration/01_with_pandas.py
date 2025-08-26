"""
Pandas + one Alloy command

Run:
  python examples/60-integration/01_with_pandas.py

Requirements:
  - pandas (see examples/requirements.txt)

Notes:
  - Shows normal data munging with a single AI step
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv


@dataclass
class Report:
    headline: str
    insights: list[str]


@command(output=Report)
def summarize_sales(stats: dict) -> str:
    return f"""
    Create a brief report with a headline and 3–5 insights.
    Data (dict): {stats}
    """


def main():
    load_dotenv()
    configure(temperature=0.2)

    # Build a small DataFrame
    df = pd.DataFrame(
        {
            "region": ["NA", "EU", "APAC", "NA", "EU"],
            "revenue": [120_000, 90_000, 60_000, 80_000, 110_000],
            "orders": [120, 90, 60, 75, 105],
        }
    )
    grouped = df.groupby("region").agg(revenue=("revenue", "sum"), orders=("orders", "sum"))
    stats = {
        "total_revenue": int(df["revenue"].sum()),
        "total_orders": int(df["orders"].sum()),
        "by_region": grouped.to_dict(orient="index"),
    }

    report = summarize_sales(stats)
    print(report.headline)
    for s in report.insights:
        print("-", s)


if __name__ == "__main__":
    main()

