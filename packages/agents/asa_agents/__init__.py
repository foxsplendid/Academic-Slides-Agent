"""asa_agents — provider-agnostic agents that produce Slide-IR (and the Hard-Stop workflow)."""

from .llm import LLM, FakeLLM
from .outline import SYSTEM_PROMPT, build_outline, build_outline_prompt
from .workflow import approve_outline, plan_outline

__all__ = [
    "LLM",
    "FakeLLM",
    "build_outline",
    "build_outline_prompt",
    "SYSTEM_PROMPT",
    "plan_outline",
    "approve_outline",
]
