"""asa_agents — provider-agnostic agents that produce Slide-IR (and the Hard-Stop workflow)."""

from .critic import critique_deck
from .deepen import build_deck_detailed
from .llm import LLM, FakeLLM
from .render_md import deck_to_markdown
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
    "critique_deck",
    "build_deck_detailed",
    "deck_to_markdown",
]
