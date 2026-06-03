"""LangGraph orchestration: outline -> Hard-Stop (interrupt) -> compile.

Per docs/SPEC.md §5, only this package imports LangGraph. The graph delivers the three headline
requirements: `interrupt()` (human Hard-Stop), a checkpointer (resume), and streaming.

The LLM call (planning) and the interrupt (approval) are deliberately in **separate nodes** so a
resume re-runs only the approval node — the expensive LLM call never fires twice.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from pptx_compiler import compile_deck
from slide_ir import Deck, GenerationState, Phase

from .llm import LLM
from .outline import build_outline


def build_graph(
    llm: LLM,
    *,
    formula_renderer=None,
    out_dir: str | Path = "exports",
    checkpointer=None,
):
    """Build and compile the orchestration graph. Inject `llm`/`formula_renderer` via closure."""
    out_dir_path = Path(out_dir)

    def plan(state: GenerationState) -> dict:
        deck = build_outline(state.evidence, state.tables, llm)  # LLM -> IR boundary (rejects non-IR)
        outline = [
            {"slide_id": s.slide_id, "layout_type": s.layout_type.value, "title": s.title}
            for s in deck.slides
        ]
        return {"slides": deck.slides, "outline": outline, "phase": Phase.AWAIT_OUTLINE_APPROVAL}

    def approval(state: GenerationState) -> dict:
        decision = interrupt({"outline": state.outline})  # Hard-Stop: pause for human approval
        edits = decision.get("edits") if isinstance(decision, dict) else None
        return {"user_approved_outline": True, "user_outline_edits": edits, "phase": Phase.MAPPING}

    def compile_slides(state: GenerationState) -> dict:
        out_dir_path.mkdir(parents=True, exist_ok=True)
        out_path = out_dir_path / f"{state.job_id}.pptx"
        compile_deck(
            Deck(deck_id=state.job_id, slides=state.slides),
            out_path,
            formula_renderer=formula_renderer,
        )
        return {"output_path": str(out_path), "phase": Phase.DONE}

    builder = StateGraph(GenerationState)
    builder.add_node("plan", plan)
    builder.add_node("approval", approval)
    builder.add_node("compile", compile_slides)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "approval")
    builder.add_edge("approval", "compile")
    builder.add_edge("compile", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())
