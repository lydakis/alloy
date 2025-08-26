"""
RAG with typed citations

Run:
  python examples/80-patterns/01_rag_citations.py

Notes:
  - Structured retrieval + citation tracking via a tool
  - Offline: export ALLOY_BACKEND=fake
"""

from dataclasses import dataclass
from alloy import command, tool, configure
from dotenv import load_dotenv


# Mock document store
DOCUMENTS = {
    "doc1": "Python was created by Guido van Rossum and released in 1991.",
    "doc2": "Python emphasizes code readability and uses indentation.",
    "doc3": "Python supports multiple programming paradigms.",
}


@tool
def search_documents(query: str, max_results: int = 3) -> list[dict]:
    """Search documents and return relevant passages."""
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


def main():
    load_dotenv()
    configure(temperature=0.2)
    result = answer_with_sources("When was Python created and by whom?")
    print(f"Answer: {result.answer}")
    print(f"Sources: {', '.join(result.citations)}")
    print(f"Confidence: {result.confidence:.1%}")


if __name__ == "__main__":
    main()

