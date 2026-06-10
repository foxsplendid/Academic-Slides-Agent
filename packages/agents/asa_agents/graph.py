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


def _asa_serde():
    """A serializer that registers our `slide_ir` types, so checkpoint resume emits no
    'unregistered type' warning and is not blocked by strict-msgpack handling."""
    import enum
    import inspect

    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    from pydantic import BaseModel

    from slide_ir import models as _m

    allowed = [
        obj
        for _, obj in inspect.getmembers(_m, inspect.isclass)
        if obj.__module__ == _m.__name__ and issubclass(obj, (BaseModel, enum.Enum))
    ]
    return JsonPlusSerializer(allowed_msgpack_modules=allowed)


def _asa_checkpointer():
    return MemorySaver(serde=_asa_serde())


def durable_checkpointer(path: str | Path):
    """A SQLite-backed checkpointer: graph state survives server restarts, so interrupted jobs can
    resume from their last completed node (true 断点续跑)."""
    import sqlite3

    from langgraph.checkpoint.sqlite import SqliteSaver

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)  # SqliteSaver serializes via its own lock
    return SqliteSaver(conn, serde=_asa_serde())

from pptx_compiler import compile_deck, lint_compiled_deck
from slide_ir import Deck, GenerationState, Phase

from .critic import critique_deck
from .llm import LLM
from .outline import build_outline
from .render_md import deck_to_markdown


def build_graph(
    llm: LLM,
    *,
    formula_renderer=None,
    out_dir: str | Path = "exports",
    checkpointer=None,
    planner=build_outline,
    style=None,
    vision_llm=None,
    icon_renderer=None,
):
    """Build and compile the orchestration graph. Inject `llm`/`formula_renderer` via closure.

    `planner(assets, tables, llm, *, feedback=None) -> Deck` defaults to the single-shot
    `build_outline`; pass `build_deck_detailed` for the two-stage detailed builder. When
    ``vision_llm`` is provided, a VLM visual critique (closed defect taxonomy) joins the quality
    loop after the deterministic checks pass.
    """
    out_dir_path = Path(out_dir)

    def plan(state: GenerationState) -> dict:
        # On a retry the prior critic findings are fed back so the LLM fixes them; the counter
        # advances exactly when feedback is consumed, so it tracks re-plans (not the initial plan).
        feedback = state.critic_findings or None
        try:  # forward per-slide progress to the custom stream so the UI can show it live
            from langgraph.config import get_stream_writer

            writer = get_stream_writer()
        except Exception:
            writer = None

        def progress(event: dict) -> None:
            if writer:
                try:
                    writer({"progress": event})
                except Exception:
                    pass

        # On a retry, hand the planner the prior slides so it can repair only the flagged ones.
        prior = state.slides if feedback else None
        deck = planner(
            state.evidence,
            state.tables,
            llm,
            feedback=feedback,
            progress=progress,
            prior_slides=prior,
            detail=state.options.get("detail", "auto"),
        )
        outline = [
            {"slide_id": s.slide_id, "layout_type": s.layout_type.value, "title": s.title}
            for s in deck.slides
        ]
        return {
            "slides": deck.slides,
            "outline": outline,
            "retry_count": state.retry_count + (1 if feedback else 0),
            "phase": Phase.OUTLINING,
        }

    def critic(state: GenerationState) -> dict:
        job_style = state.style or style
        findings = critique_deck(state.slides, state.evidence)
        # Quality loop, cheapest first: IR checks -> exact geometry lint -> (opt-in) VLM visual check.
        # The lint/VLM stages compile a throwaway render; both fail open (a broken check never blocks).
        if not findings:
            lint_dir = out_dir_path / "runs" / state.job_id
            lint_pptx = lint_dir / "lint.pptx"
            try:
                lint_dir.mkdir(parents=True, exist_ok=True)
                deck = Deck(deck_id=state.job_id, slides=state.slides)
                resolver = {a.asset_id: a.content_ref for a in state.evidence if a.kind == "figure"}
                compile_deck(deck, lint_pptx, asset_resolver=resolver, style=job_style)  # no formula sidecar: fast
                findings = lint_compiled_deck(deck, lint_pptx)
            except Exception:
                findings = []
            if not findings and vision_llm is not None and state.options.get("vlm_critic", False):
                try:
                    from .visual_critic import visual_critique

                    findings = visual_critique(state.slides, lint_pptx, vision_llm, lint_dir / "vlm")
                except Exception:
                    findings = []
        return {"critic_findings": findings, "phase": Phase.CRITIQUING}

    def after_critic(state: GenerationState) -> str:
        # Retry only while there are findings AND budget remains; otherwise hand the human a deck.
        if state.critic_findings and state.retry_count < state.max_retries:
            return "plan"
        return "approval"

    def approval(state: GenerationState) -> dict:
        decision = interrupt({"outline": state.outline})  # Hard-Stop: pause for human approval
        approved = bool(decision.get("approved", True)) if isinstance(decision, dict) else True
        edits = decision.get("edits") if isinstance(decision, dict) else None
        if not approved:  # human rejected: feed their reason back as findings and replan
            feedback = (decision.get("feedback") or "").strip() if isinstance(decision, dict) else ""
            findings = [f"用户退回大纲: {feedback or '请改进整体结构与内容'}"]
            return {"user_approved_outline": False, "critic_findings": findings, "phase": Phase.OUTLINING}
        return {"user_approved_outline": True, "user_outline_edits": edits, "phase": Phase.MAPPING}

    def after_approval(state: GenerationState) -> str:
        return "compile" if state.user_approved_outline else "plan"

    def compile_slides(state: GenerationState) -> dict:
        run_dir = out_dir_path / "runs" / state.job_id  # per-run isolation (compare agent modes)
        run_dir.mkdir(parents=True, exist_ok=True)
        out_path = run_dir / "out.pptx"
        deck = Deck(deck_id=state.job_id, slides=state.slides)
        resolver = {a.asset_id: a.content_ref for a in state.evidence if a.kind == "figure"}
        icon_resolver = icon_renderer.render if icon_renderer is not None else None
        renderer = formula_renderer
        if state.options.get("native_formula") and hasattr(renderer, "native_omml"):
            import copy

            renderer = copy.copy(renderer)  # per-job opt-in without mutating the shared renderer
            renderer.native_omml = True
        compile_deck(
            deck,
            out_path,
            formula_renderer=renderer,
            asset_resolver=resolver,
            style=state.style or style,
            icon_resolver=icon_resolver,
        )
        try:  # human-readable + machine artifacts for diffing runs (best-effort)
            (run_dir / "deck.json").write_text(deck.model_dump_json(indent=2), encoding="utf-8")
            (run_dir / "deck.md").write_text(deck_to_markdown(deck), encoding="utf-8")
        except Exception:
            pass
        return {"output_path": str(out_path), "phase": Phase.DONE}

    builder = StateGraph(GenerationState)
    builder.add_node("plan", plan)
    builder.add_node("critic", critic)
    builder.add_node("approval", approval)
    builder.add_node("compile", compile_slides)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "critic")
    builder.add_conditional_edges("critic", after_critic, {"plan": "plan", "approval": "approval"})
    builder.add_conditional_edges("approval", after_approval, {"compile": "compile", "plan": "plan"})
    builder.add_edge("compile", END)
    return builder.compile(checkpointer=checkpointer or _asa_checkpointer())
