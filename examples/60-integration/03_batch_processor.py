"""
Batch processing with concurrent.futures

Run:
  python examples/60-integration/03_batch_processor.py

Notes:
  - Demonstrates parallel processing of inputs with commands
  - Uses ThreadPool for portability across environments
  - Offline: export ALLOY_BACKEND=fake
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from alloy import command, configure
from dotenv import load_dotenv


@dataclass
class Summary:
    id: int
    verdict: str


@command(output=Summary)
def review_ticket(ticket_id: int, description: str) -> str:
    return f"""
    Review the support ticket and return a verdict:
    - "resolved" if no action needed
    - "needs_followup" with a brief reason otherwise

    ticket_id: {ticket_id}
    description: {description}
    """


def process_batch(tickets: list[tuple[int, str]], max_workers: int = 4) -> list[Summary]:
    results: list[Summary] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(review_ticket, tid, desc): tid for (tid, desc) in tickets}
        for f in as_completed(futs):
            try:
                results.append(f.result())
            except Exception as e:
                print("Error:", e)
    return results


def main():
    load_dotenv()
    configure(temperature=0.2)
    inputs = [
        (1, "Customer reports duplicate email notifications."),
        (2, "App loads slowly on first launch."),
        (3, "Typo on billing page header."),
    ]
    out = process_batch(inputs)
    for s in out:
        print(s)


if __name__ == "__main__":
    main()

