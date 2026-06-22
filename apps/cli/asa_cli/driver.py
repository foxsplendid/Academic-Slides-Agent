"""The thin headless seam: build the SAME compiled graph the API uses, and the SAME initial state
the upload handler builds. Nothing here reimplements the pipeline — it only composes existing parts.

The graph wiring mirrors ``asa_api.server.build_default_app`` (provider_from_env LLM, the two-stage
``build_deck_detailed`` planner, a durable SqliteSaver checkpointer, formula + icon renderers), but
returns the compiled graph for direct ``invoke``/``get_state``/resume rather than a FastAPI app. A
durable checkpointer is used so the ``outline`` -> ``build --from-outline`` round-trip can resume the
interrupted run from disk in a fresh process (same out_dir + same thread_id = same paused run).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from ingestion import ingest
from slide_ir import GenerationState


def load_env(path: Optional[str | Path] = None) -> None:
    """Best-effort load of a local ``.env`` (no-op if python-dotenv or the file is absent)."""
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    try:
        load_dotenv(path) if path is not None else load_dotenv()
    except Exception:
        pass


def ingest_to_state(
    source: str | Path,
    *,
    job_id: str,
    out_dir: str | Path,
    style: Optional[str] = None,
    options: Optional[dict] = None,
):
    """Ingest a handoff dir (or PDF/zip/...) and build the initial ``GenerationState`` exactly as the
    API upload handler does (apps/api/asa_api/app.py:300-314). Returns ``(state, IngestResult)``."""
    cache = Path(out_dir) / "papers"  # shared content-addressed parse cache, matching the API
    workspace = Path(out_dir) / "uploads" / job_id
    workspace.mkdir(parents=True, exist_ok=True)
    result = ingest(str(source), workspace=workspace, cache_dir=cache)
    opts = options or {
        "detail": "auto",
        "premium": True,
        "native_formula": True,
        "vlm_critic": False,
    }
    state = GenerationState(
        job_id=job_id,
        evidence=result.assets,
        tables=result.tables,
        style=style,
        options=opts,
    )
    return state, result


def build_cli_graph(
    *,
    out_dir: str | Path,
    llm=None,
    formula_renderer=None,
    style: Optional[str] = None,
    planner=None,
):
    """Build the production graph for a headless run. Mirrors ``build_default_app`` wiring but returns
    the ``CompiledGraph`` directly. ``llm``/``formula_renderer`` are injected by tests (a FakeLLM);
    at runtime they default to the env-configured provider and the matplotlib/MathJax renderer.
    ``planner`` defaults to the two-stage ``build_deck_detailed``; tests inject the single-shot
    ``build_outline`` so one scripted FakeLLM response drives the whole plan."""
    if llm is None:
        from asa_providers import provider_from_env  # lazy: needs a provider SDK only at runtime

        llm = provider_from_env()
    if formula_renderer is None:
        try:
            from formula_render import default_formula_renderer

            formula_renderer = default_formula_renderer()
        except Exception:
            formula_renderer = None

    from asa_agents import build_deck_detailed
    from asa_agents.graph import build_graph, durable_checkpointer

    resolved_style = style if style is not None else os.environ.get("ASA_STYLE")
    resolved_planner = planner if planner is not None else build_deck_detailed

    checkpointer = None
    try:  # durable checkpoints let `outline` pause and `build --from-outline` resume in a new process
        checkpointer = durable_checkpointer(Path(out_dir) / "checkpoints.sqlite")
    except Exception:
        checkpointer = None  # fall back to in-memory MemorySaver inside build_graph

    icon_renderer = None
    try:
        from formula_render import default_icon_renderer

        icon_renderer = default_icon_renderer(Path(out_dir) / "icons")
    except Exception:
        icon_renderer = None

    return build_graph(
        llm,
        formula_renderer=formula_renderer,
        out_dir=out_dir,
        planner=resolved_planner,
        style=resolved_style,
        checkpointer=checkpointer,
        icon_renderer=icon_renderer,
    )


def cfg(thread_id: str) -> dict:
    """The LangGraph thread config — thread_id is the job_id, exactly as the API uses it."""
    return {"configurable": {"thread_id": thread_id}}


def field(obj, name, default=None):
    """Read a field from a dict or a model (LangGraph state round-trips to either shape)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)
