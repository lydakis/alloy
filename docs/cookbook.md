# Cookbook

Practical, pipeline-ready demos you can copy‑paste.

## Turn CSVs into API calls

```python
from alloy import command
import pandas as pd

@command(output=list[dict])
def csv_to_api(df: pd.DataFrame, endpoint_example: str) -> str:
    """Intelligently map CSV columns to API format."""
    return f"Map this data {df.head()} to match API: {endpoint_example}"

# Any CSV → Any API
df = pd.read_csv("customers.csv")
payloads = csv_to_api(df, "POST /customers {fullName, emailAddress, subscriptionTier}")
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
def interview_to_spec(transcript: str) -> str:
    return f"Extract feature requirements from: {transcript}"
```

## PR review bot with tools

```python
from alloy import command, tool

@tool
def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

@command(output=dict, tools=[read_file])
def review_pr(diff: str, pr_description: str) -> str:
    return f"Review this PR considering our patterns: {pr_description}\nDiff: {diff}"
```

See [examples/](https://github.com/lydakis/alloy/tree/main/examples) for runnable versions and more demos.

## Deep Agent (planning, subagents, workspace)

Pattern: compose primitives to build a multi‑phase agent that plans, spawns focused subagents, writes artifacts to a shared workspace, and compiles a final report — while keeping Alloy as a library (no framework glue).

Run (real model):

```
python examples/90-advanced/01_deep_agents.py
```

No API keys? You can preview behavior without network by setting `ALLOY_BACKEND=fake` when running the example.

Building blocks:

- plan_todo: no‑op tool that records a 3–7 bullet plan (contract‑enforced) for traceability.
- Filesystem tools: `write_file`, `append_file`, `read_file`, `list_files` with path safety and size/limit guards.
- spawn_subagent: tool that calls `ask(...)` with a focused system + limited tools for narrow subtasks.
- compile_report: synthesizes `files/notes/*.md` into `files/REPORT.md` with a "writer" system.
- require_report: DBC check forcing the final artifact before completion.

Orchestrator (sketch):

```python
from dataclasses import dataclass
from alloy import command

@dataclass
class AgentResult:
    summary: str
    files: list[str]

@command(output=AgentResult, tools=[...], system="...rules...")
def deep_research(goal: str) -> str:
    return """
      Objective: {goal}
      - plan_todo to outline 3–7 bullets
      - write notes to files/notes/*.md; use spawn_subagent for narrow tasks
      - compile_report(title=...) → files/REPORT.md
      - require_report() must pass before returning
      Return JSON {summary, files}
    """.strip().format(goal=goal)
```

Full example: [`examples/90-advanced/01_deep_agents.py`](https://github.com/lydakis/alloy/blob/main/examples/90-advanced/01_deep_agents.py).
