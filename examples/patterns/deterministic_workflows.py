"""
Patterns: deterministic orchestration with commands

Run:
  # Load API keys from .env (e.g., OPENAI_API_KEY)
  python examples/patterns/deterministic_workflows.py

Notes:
- Uses @command for typed steps (research -> write -> edit)
- Demonstrates parallel execution via .async_() + asyncio.gather
- Implements a simple evaluate→improve loop with PASS/IMPROVE logic
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from alloy import command


@command(output=list[str])
def research(topic: str) -> str:
    return """
        Research the topic strictly using your prior knowledge. Return 5 bullet points of factual
        insights only. Use short, precise bullets.
        Topic: {topic}
        """.strip().format(
        topic=topic
    )


@command(output=str)
def write_overview(notes: str) -> str:
    return """
        Write a concise, well-structured 3‑paragraph overview from the provided notes. Avoid fluff;
        prefer precise claims. Return plain text.
        Notes:
        {notes}
        """.strip().format(
        notes=notes
    )


@command(output=str)
def edit_for_clarity(draft: str) -> str:
    return """
        Improve clarity and flow of the draft. Tighten prose, remove repetition. Return the full
        improved draft.
        Draft:
        {draft}
        """.strip().format(
        draft=draft
    )


@command(output=list[str])
def brainstorm_angles(seed: str) -> str:
    return f"Propose 5 distinct angles for a blog post title about: {seed}"


@command(output=list[str])
def brainstorm_seo_titles(seed: str) -> str:
    return """
        Propose 5 concise, SEO‑friendly titles (<= 60 chars) for a blog post about: {seed}.
        Return a JSON array of strings only.
        """.strip().format(
        seed=seed
    )


@dataclass
class LoopSettings:
    max_iters: int = 4


settings = LoopSettings()


@command(output=str)
def evaluate(draft: str) -> str:
    return """
        Assess whether the draft meets all criteria: (1) factual, (2) clear, (3) actionable.
        Answer strictly with 'PASS' or 'IMPROVE' on the first line, then 1‑2 bullet points if
        'IMPROVE'.
        Draft:
        {draft}
        """.strip().format(
        draft=draft
    )


@command(output=str)
def improve(draft: str, feedback: str) -> str:
    return """
        Given a draft and evaluator feedback, produce an improved full draft. Address each point
        concisely. Return the entire improved draft.
        Draft:
        {draft}
        Evaluator feedback:
        {feedback}
        """.strip().format(
        draft=draft, feedback=feedback
    )


async def chain_example(topic: str) -> str:
    notes = "\n".join(research(topic))
    draft = write_overview(notes)
    return edit_for_clarity(draft)


async def parallel_example(seed: str) -> list[str]:
    # Run both brainstorm commands concurrently via async_()
    a_task = brainstorm_angles.async_(seed)
    b_task = brainstorm_seo_titles.async_(seed)
    a, b = await asyncio.gather(a_task, b_task)
    # Render as joined text blocks for display
    return ["\n".join(a), "\n".join(b)]


async def evaluate_improve(initial_brief: str, *, max_iters: Optional[int] = None) -> str:
    if max_iters is None:
        max_iters = settings.max_iters
    # First draft directly from the brief
    draft = write_overview(initial_brief)
    for _ in range(max_iters):
        verdict_text = evaluate(draft)
        verdict_first = (verdict_text or "").strip().splitlines()[0].upper()
        if verdict_first.startswith("PASS"):
            return draft
        feedback_lines = (verdict_text or "").splitlines()[1:]
        feedback = "\n".join(feedback_lines)
        draft = improve(draft, feedback)
    return draft


async def main() -> None:
    load_dotenv()
    # Optional: tweak defaults
    # configure(model="gpt-5-mini", temperature=0.2)

    chained = await chain_example("Zero‑downtime blue/green deploys on Fargate")
    print("=== CHAINED ===\n", chained)

    a, b = await parallel_example("vector DBs for retrieval agents")
    print("=== PARALLEL (A) ===\n", a)
    print("=== PARALLEL (B) ===\n", b)

    looped = await evaluate_improve("Write a short guide to prompt caching for production apps.")
    print("=== LOOPED ===\n", looped)


if __name__ == "__main__":
    asyncio.run(main())
