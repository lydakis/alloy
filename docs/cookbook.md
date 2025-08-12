# Cookbook

Practical, pipeline-ready demos you can copy‑paste.

## Turn CSVs into API calls

```python
from alloy import command
import pandas as pd

@command(output=list[dict])
def CSVToAPI(df: pd.DataFrame, endpoint_example: str) -> str:
    """Intelligently map CSV columns to API format."""
    return f"Map this data {df.head()} to match API: {endpoint_example}"

# Any CSV → Any API
df = pd.read_csv("customers.csv")
payloads = CSVToAPI(df, "POST /customers {fullName, emailAddress, subscriptionTier}")
for p in payloads:
    requests.post("https://api.your-saas.com/customers", json=p)
```

## Customer interview → Feature spec

```python
from dataclasses import dataclass
from alloy import command

@dataclass
class FeatureSpec:
    user_story: str
    acceptance_criteria: list[str]
    technical_requirements: list[str]
    effort_estimate: str
    risks: list[str]

@command(output=FeatureSpec)
def InterviewToSpec(transcript: str) -> str:
    return f"Extract feature requirements from: {transcript}"
```

## PR review bot with tools

```python
from alloy import command
from alloy.tool import tool

@tool
def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

@command(output=dict, tools=[read_file])
def ReviewPR(diff: str, pr_description: str) -> str:
    return f"Review this PR considering our patterns: {pr_description}\nDiff: {diff}"
```

See `examples/` for runnable versions and more demos.
