"""
Alloy: Agent-first programming for Python

A clean, Pythonic API for AI agents with first-class support for:
- Agents as first-class citizens
- Structured output with automatic parsing
- Design-by-contract patterns
- Pipeline operations
- Natural language commands
"""

from .core.agent import Agent
from .core.memory import Memory
from .core.agentic_loop import tool
from .core.command import command
from .core.pipeline import pipeline, Pipeline, P, pipe, from_value, start_pipeline
from .core.contracts import (
    require, ensure, invariant, ContractViolation,
    enable_contracts, disable_contracts, contracts_enabled
)

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "Memory", 
    "tool",
    "command",
    "pipeline",
    "Pipeline", 
    "P",
    "pipe",
    "from_value",
    "start_pipeline",
    "require",
    "ensure", 
    "invariant",
    "ContractViolation",
    "enable_contracts",
    "disable_contracts",
    "contracts_enabled",
]