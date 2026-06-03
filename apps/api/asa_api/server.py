"""Default app wiring — one call to assemble a runnable app.

Defaults the LLM to ``provider_from_env()`` and the formula renderer to the matplotlib renderer,
both imported lazily so importing this module needs no provider SDK (tests inject a ``FakeLLM``).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .app import create_app


def build_default_app(*, llm=None, formula_renderer=None, out_dir: Optional[str | Path] = None):
    if llm is None:
        from asa_providers import provider_from_env  # lazy: needs a provider SDK only at runtime

        llm = provider_from_env()
    if formula_renderer is None:
        from formula_render import MatplotlibFormulaRenderer  # lazy

        formula_renderer = MatplotlibFormulaRenderer()
    resolved_out = out_dir or os.environ.get("ASA_OUT_DIR", "exports")
    return create_app(llm, formula_renderer=formula_renderer, out_dir=resolved_out)
