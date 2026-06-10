"""formula_render — LaTeX -> image rendering behind the compiler's FormulaRenderer interface."""

from .auto_renderer import AutoFormulaRenderer, default_formula_renderer, is_advanced
from .icon_renderer import ICON_WHITELIST, IconRenderer, default_icon_renderer
from .mathjax_renderer import MathJaxFormulaRenderer
from .matplotlib_renderer import MatplotlibFormulaRenderer

__all__ = [
    "MatplotlibFormulaRenderer",
    "MathJaxFormulaRenderer",
    "AutoFormulaRenderer",
    "default_formula_renderer",
    "is_advanced",
    "IconRenderer",
    "default_icon_renderer",
    "ICON_WHITELIST",
]
