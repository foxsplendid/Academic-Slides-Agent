"""formula_render — LaTeX -> image rendering behind the compiler's FormulaRenderer interface."""

from .auto_renderer import AutoFormulaRenderer, default_formula_renderer, is_advanced
from .mathjax_renderer import MathJaxFormulaRenderer
from .matplotlib_renderer import MatplotlibFormulaRenderer

__all__ = [
    "MatplotlibFormulaRenderer",
    "MathJaxFormulaRenderer",
    "AutoFormulaRenderer",
    "default_formula_renderer",
    "is_advanced",
]
