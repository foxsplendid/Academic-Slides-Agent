"""Default app wiring — one call to assemble a runnable app.

Defaults the LLM to ``provider_from_env()`` and the formula renderer to the matplotlib renderer,
both imported lazily so importing this module needs no provider SDK (tests inject a ``FakeLLM``).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .app import create_app


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


def build_default_app(*, llm=None, formula_renderer=None, out_dir: Optional[str | Path] = None):
    if llm is None:
        from asa_providers import provider_from_env  # lazy: needs a provider SDK only at runtime

        llm = provider_from_env()
    if formula_renderer is None:
        from formula_render import default_formula_renderer  # lazy; MathJax tier if Node sidecar present

        formula_renderer = default_formula_renderer()
    resolved_out = out_dir or os.environ.get("ASA_OUT_DIR", "exports")
    from asa_agents import build_deck_detailed  # two-stage detailed planner for production runs

    return create_app(
        llm,
        formula_renderer=formula_renderer,
        out_dir=resolved_out,
        planner=build_deck_detailed,
        style=os.environ.get("ASA_STYLE"),  # style profile name (default: academic)
    )
