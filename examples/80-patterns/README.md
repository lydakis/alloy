# 80 — Patterns

- Purpose: Reusable orchestration patterns expressed with commands/tools.
- When to use: RAG, self-refine, guardrails, streaming, retry.
- Notes: Python remains the control layer; models provide intelligence.
- Offline: `export ALLOY_BACKEND=fake`.

Files:
- `01_rag_citations.py` — RAG with citations
- `02_self_refine.py` — iterative improvement loop
- `03_pii_sanitize.py` — PII guardrail via tool
- `04_streaming_updates.py` — streaming text-only
- `05_retry_strategies.py` — retry patterns
- `06_stateful_assistant.py` — file-backed memory (facts + summary)
- `07_conversation_history.py` — manage rolling chat history across turns
