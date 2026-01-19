"""
Patterns: deep agent (planning, subagents, filesystem)

Run:
  # Load API keys from .env (e.g., OPENAI_API_KEY)
  # Optional: raise tool loop limit via env or configure(max_tool_turns=...)
  #   export ALLOY_MAX_TOOL_TURNS=8
  python examples/90-advanced/01_deep_agents.py

Notes:
- Implements a lightweight “deep agent” pattern inspired by Claude Code:
  - A detailed system prompt
  - A planning tool (no‑op Todo, acts as context scaffolding)
  - Sub‑agents via a tool that calls ask() with a focused prompt
  - Filesystem tools for shared workspace memory (notes, report)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from alloy import command, tool, ask, configure, require, ensure

# Workspace root for this example (local to this folder)
WS_ROOT = Path(__file__).with_name("_workspace_deep_agents")
WS_ROOT.mkdir(parents=True, exist_ok=True)


#
# Utilities
#


def _safe_path(rel: str) -> Path:
    """Resolve a path safely beneath WS_ROOT."""
    # Normalize and prevent escaping outside WS_ROOT
    rel = rel.strip().lstrip("/")
    p = (WS_ROOT / rel).resolve()
    if not str(p).startswith(str(WS_ROOT.resolve())):
        # Fall back to WS_ROOT if the model tries to escape
        return WS_ROOT / "blocked_path.txt"
    return p


#
# Tools: Planning (no‑op), Filesystem, Subagents
#


@tool
@require(lambda ba: bool(str(ba.arguments.get("items", "")).strip()), "must include plan items")
def plan_todo(items: str) -> str:
    """Record a short Todo plan (3-7 bullets). No side effects; returns the plan back."""
    # Intentionally returns the plan unmodified for context engineering
    return items.strip()


@tool
@require(lambda ba: bool(str(ba.arguments.get("path", "")).strip()), "must provide path")
def write_file(path: str, content: str) -> str:
    """Write content to a file under the workspace; creates parent dirs if needed."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content or "", encoding="utf-8")
    return f"wrote {len(content or '')} bytes to {p.relative_to(WS_ROOT)}"


@tool
@require(lambda ba: bool(str(ba.arguments.get("path", "")).strip()), "must provide path")
def append_file(path: str, text: str) -> str:
    """Append a line of text to a file under the workspace."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write((text or "") + ("\n" if text and not text.endswith("\n") else ""))
    return f"appended to {p.relative_to(WS_ROOT)}"


@tool
@require(lambda ba: bool(str(ba.arguments.get("path", "")).strip()), "must provide path")
def read_file(path: str) -> str:
    """Read a text file from the workspace and return its content."""
    p = _safe_path(path)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


@tool
def list_files(prefix: str = "") -> str:
    """List files in the workspace (optionally filter by prefix). Returns newline-separated paths."""
    base = _safe_path(prefix) if prefix else WS_ROOT
    if base.is_file():
        base = base.parent
    items: list[str] = []
    try:
        for p in base.rglob("*"):
            if p.is_file():
                items.append(str(p.relative_to(WS_ROOT)))
    except Exception:
        pass
    return "\n".join(sorted(items))


@tool
@ensure(lambda ok: ok is True, "create files/REPORT.md first")
def require_report() -> bool:
    """Validate that files/REPORT.md exists. Returns True if present, else fails contract."""
    return (_safe_path("files/REPORT.md")).exists()


SUBAGENT_SYSTEM = (
    "You are a focused sub-agent. Be concise, accomplish the assigned subtask, "
    "and write any intermediate notes to files if asked via tools."
)


REPORT_SYSTEM = (
    "You are a precise technical writer. Produce a clean Markdown report with the requested "
    "sections only, no extra commentary."
)


@tool
def compile_report(title: str = "Deep Agent Planning Approaches") -> str:
    """Compile final Markdown report from notes/*.md and save to files/REPORT.md. Returns path."""
    notes_dir = _safe_path("files/notes")
    notes: list[str] = []
    if notes_dir.exists():
        for p in sorted(notes_dir.glob("*.md")):
            try:
                notes.append(f"# Note: {p.name}\n\n" + p.read_text(encoding="utf-8"))
            except Exception:
                continue
    notes_text = "\n\n\n".join(notes) if notes else "(no notes)"
    prompt = (
        f"Title: {title}\n\n"
        "Synthesize a final report with sections: \n"
        "1) Overview\n2) Key Findings (bulleted, cite note filenames)\n"
        "3) Risks & Gaps\n4) Next Steps\n\n"
        "Be concise and concrete.\n\nNotes:\n" + notes_text
    )
    content = ask(prompt, tools=None, default_system=REPORT_SYSTEM)
    out = _safe_path("files/REPORT.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return str(out.relative_to(WS_ROOT))


@tool
@require(lambda ba: bool(str(ba.arguments.get("goal", "")).strip()), "must include goal")
@ensure(lambda s: isinstance(s, str) and len(s) > 0, "must return a result summary")
def spawn_subagent(goal: str, context_hint: str = "") -> str:
    """Spawn a focused sub-agent for a narrow goal. Returns a concise summary of findings."""
    # Expose only a safe subset of tools to subagents (no further spawn to avoid deep recursion)
    sub_tools = [plan_todo, write_file, append_file, read_file, list_files]
    prompt = (
        f"Subtask goal: {goal}\n"
        f"Context hint: {context_hint}\n"
        "Use plan_todo to outline your steps briefly, then execute. Save notes under notes/*.md."
    )
    return ask(prompt, tools=sub_tools, context=None, default_system=SUBAGENT_SYSTEM)


#
# Orchestrator command: Deep Research
#


DEEP_SYSTEM = (
    "You are a diligent, multi-step agent. Follow these rules strictly:\n"
    "- Start each phase by calling plan_todo with 3-7 bullets.\n"
    "- Create and use a shared workspace (files/notes) via tools.\n"
    "- Split work with spawn_subagent for narrow subtasks.\n"
    "- Keep messages concise; do not repeat long content in chat when it can be saved to files.\n"
    "- Always call compile_report(title=...) to create files/REPORT.md with final synthesis.\n"
    "- Before returning, call require_report(); if it fails, run compile_report and retry.\n"
    "- When done, return a short summary and enumerate created files."
)


@dataclass
class AgentResult:
    summary: str
    files: list[str]


@command(
    output=AgentResult,
    tools=[
        plan_todo,
        write_file,
        append_file,
        read_file,
        list_files,
        compile_report,
        require_report,
        spawn_subagent,
    ],
    system=DEEP_SYSTEM,
)
def deep_research(goal: str) -> str:
    """Research deeply and synthesize a short report saved to files/REPORT.md. Return summary+files."""
    return """
    Objective: {goal}

    Expectations:
    - Use plan_todo to outline a plan (no-op tool, just returns the plan) and keep yourself on track.
    - Save rough notes under files/notes/*.md as you progress. Keep each note short and focused.
    - When a subtopic needs dedicated focus, call spawn_subagent(goal=<narrow subgoal>, context_hint=<why>). Let it plan and write notes; you can later read those notes via read_file.
    - Assemble a final report at files/REPORT.md by calling compile_report(title=...). The report must include sections: Overview, Key Findings (bullets with citations to your notes files), Risks/Gaps, and Next Steps.
    - Before returning, call require_report(); if it fails, run compile_report and call require_report again.
    - Prefer using read_file/list_files over pasting large content in the chat.

    Output contract:
    - Return a JSON object with:\n      - summary: 1-2 sentences summarizing the outcome\n      - files: an array of workspace file paths you created (e.g., ["files/REPORT.md", "files/notes/a.md"]).
    """.strip().format(goal=goal)


def main() -> None:
    load_dotenv()
    # Tighten style a bit and allow longer tool loops for the deep flow.
    # You can also do this via env: export ALLOY_MAX_TOOL_TURNS=8
    # Use GPT‑5 by default; override with ALLOY_MODEL if set
    model = os.environ.get("ALLOY_MODEL", "gpt-5")
    configure(model=model, temperature=0.2, max_tool_turns=8)

    # Seed a clean workspace structure
    (WS_ROOT / "files" / "notes").mkdir(parents=True, exist_ok=True)
    # Provide a starting BRIEF to anchor context if the agent wants to open it
    (WS_ROOT / "files" / "BRIEF.md").write_text(
        "Project brief will be refined by the agent.\n", encoding="utf-8"
    )

    result = deep_research(
        "Survey top approaches for long-horizon planning in LLM agents and summarize tradeoffs."
    )

    print("Summary:", result.summary)
    print("Files:\n- " + ("\n- ".join(result.files) if result.files else "(none)"))


if __name__ == "__main__":
    main()
