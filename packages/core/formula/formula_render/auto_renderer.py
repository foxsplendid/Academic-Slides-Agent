"""Tiered formula rendering: matplotlib for simple math, MathJax for advanced (chemistry/matrices)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .matplotlib_renderer import MatplotlibFormulaRenderer

# Constructs matplotlib mathtext can't handle → route straight to MathJax.
_ADVANCED = re.compile(r"\\ce\b|\\begin\{|\\\\|\\(?:p|b|v|V|B)?matrix|\\align|\\substack|\\xrightarrow")


def is_advanced(latex: str) -> bool:
    return bool(_ADVANCED.search(latex))


class AutoFormulaRenderer:
    """Pick a backend per formula: advanced → MathJax (if available); else matplotlib; with the other
    as a fallback. Implements the compiler's ``to_image(latex) -> Path | None`` protocol."""

    def __init__(self, *, simple=None, advanced=None) -> None:
        self.simple = simple or MatplotlibFormulaRenderer()
        self.advanced = advanced  # a MathJaxFormulaRenderer, or None when Node/sidecar is absent

    def to_image(self, latex: str) -> Optional[Path]:
        if self.advanced is not None and is_advanced(latex):
            img = self.advanced.to_image(latex)
            if img is not None:
                return img
        img = self.simple.to_image(latex)
        if img is not None:
            return img
        if self.advanced is not None:  # matplotlib couldn't parse it → last-resort MathJax
            return self.advanced.to_image(latex)
        return None


def default_formula_renderer(out_dir: str | Path | None = None) -> AutoFormulaRenderer:
    """Build the tiered renderer, enabling the MathJax tier only when the Node sidecar is available."""
    from .mathjax_renderer import MathJaxFormulaRenderer

    advanced = MathJaxFormulaRenderer(out_dir) if MathJaxFormulaRenderer.available() else None
    return AutoFormulaRenderer(advanced=advanced)
