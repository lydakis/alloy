# Flagship Examples

These are small, copy‑pasteable examples that demonstrate Alloy’s core patterns. Each snippet links to a runnable script under `examples/`.

Tip
- Install optional deps: `pip install -r examples/requirements.txt`
- Pick a model (e.g., `export ALLOY_MODEL=gpt-5-mini`) and set your provider key
- Offline mode: `export ALLOY_BACKEND=fake`

## Ask: exploratory

Path: `examples/00-explore/01_ask_basic.py`

```python
from alloy import ask
from dotenv import load_dotenv

def main():
    load_dotenv()
    answer = ask("What are the main components of a REST API?")
    print(answer)

if __name__ == "__main__":
    main()
```

## First command: text output

Path: `examples/10-commands/01_first_command.py`

```python
from alloy import command, configure
from dotenv import load_dotenv

@command  # default typed output is str
def summarize(text: str) -> str:
    return f"Summarize in exactly 3 bullets:\n\n{text}"

def main():
    load_dotenv()
    configure(temperature=0.2)
    print(summarize("REST APIs use HTTP methods, resources, and representations."))

if __name__ == "__main__":
    main()
```

## Typed output: dataclass

Path: `examples/20-typed/02_dataclass_output.py`

```python
from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv

@dataclass
class ArticleSummary:
    title: str
    key_points: list[str]
    reading_time_minutes: int

@command(output=ArticleSummary)
def summarize_article(text: str) -> str:
    return f"""
    Read the article and produce:
    - title: concise title
    - key_points: 3–5 short bullets
    - reading_time_minutes: integer estimate

    Article:
    {text}
    """

def main():
    load_dotenv()
    configure(temperature=0.2)
    res = summarize_article("Python emphasizes code readability…")
    print("Title:", res.title)

if __name__ == "__main__":
    main()
```

## Contracts: validate → save workflow

Path: `examples/40-contracts/02_workflow_contracts.py`

```python
from alloy import command, tool, require, ensure, configure
from dotenv import load_dotenv
import datetime

@tool
@ensure(lambda d: isinstance(d, dict) and "validated_at" in d, "Must add validated_at timestamp")
def validate_data(data: dict) -> dict:
    data = dict(data)
    data["validated_at"] = datetime.datetime.utcnow().isoformat()
    return data

@tool
@require(lambda ba: "validated_at" in ba.arguments.get("data", {}), "Run validate_data first")
@ensure(lambda ok: ok is True, "Save must succeed")
def save_to_production(data: dict) -> bool:
    print(f"Saving to production: {data}")
    return True

@command(output=str, tools=[validate_data, save_to_production])
def process_order(order: dict) -> str:
    return f"""
    Process this order through our workflow:
    1. Validate the data (adds timestamp)
    2. Save to production

    Order: {order}

    Return a summary of actions taken.
    """
```

## RAG: answer with citations

Path: `examples/80-patterns/01_rag_citations.py`

```python
from dataclasses import dataclass
from alloy import command, tool, configure

DOCUMENTS = {
    "doc1": "Python was created by Guido van Rossum and released in 1991.",
    "doc2": "Python emphasizes code readability and uses indentation.",
    "doc3": "Python supports multiple programming paradigms.",
}

@tool
def search_documents(query: str, max_results: int = 3) -> list[dict]:
    results = []
    for doc_id, content in DOCUMENTS.items():
        if any(word.lower() in content.lower() for word in query.split()):
            results.append({"id": doc_id, "content": content})
    return results[: int(max_results)]

@dataclass
class AnswerWithCitations:
    answer: str
    citations: list[str]
    confidence: float

@command(output=AnswerWithCitations, tools=[search_documents])
def answer_with_sources(question: str) -> str:
    return f"""
    Answer this question using search_documents tool:
    {question}

    Include specific citations (document IDs) for each claim.
    Rate your confidence 0.0-1.0 based on source quality.
    """
```

Further
- See the full suite under `examples/` for composition, integrations, providers, patterns, and advanced flows (deep agents, OCR, observability, evals).
