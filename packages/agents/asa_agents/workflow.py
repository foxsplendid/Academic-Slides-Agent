"""Hard-Stop workflow modeled as explicit GenerationState transitions.

LangGraph's ``interrupt()`` will wrap these in a later change; as pure functions they are testable
now without any orchestration framework.
"""

from __future__ import annotations

from typing import Optional

from slide_ir import EvidenceAsset, GenerationState, Phase, TableBlock

from .llm import LLM
from .outline import build_outline


def plan_outline(
    state: GenerationState,
    assets: list[EvidenceAsset],
    tables: list[TableBlock],
    llm: LLM,
) -> GenerationState:
    """Produce the outline (Slide-IR) and pause at the Hard-Stop for human approval."""
    deck = build_outline(assets, tables, llm)
    state.slides = deck.slides
    state.outline = [
        {"slide_id": s.slide_id, "layout_type": s.layout_type.value, "title": s.title}
        for s in deck.slides
    ]
    state.phase = Phase.AWAIT_OUTLINE_APPROVAL
    return state


def approve_outline(
    state: GenerationState, *, edited_outline: Optional[list[dict]] = None
) -> GenerationState:
    """Human approves (optionally edits) the outline; advance past the Hard-Stop."""
    state.user_approved_outline = True
    if edited_outline is not None:
        state.user_outline_edits = edited_outline
    state.phase = Phase.MAPPING
    return state
