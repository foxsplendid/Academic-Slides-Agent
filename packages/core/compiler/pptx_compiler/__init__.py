"""pptx_compiler — deterministic Slide-IR -> native .pptx rendering."""

from .compiler import compile_deck
from .formula_renderer import FormulaRenderer, NullFormulaRenderer
from .lint import lint_compiled_deck
from .style import ACADEMIC, MODERN_TEAL, StyleProfile, get_style

__all__ = [
    "compile_deck",
    "lint_compiled_deck",
    "FormulaRenderer",
    "NullFormulaRenderer",
    "StyleProfile",
    "get_style",
    "ACADEMIC",
    "MODERN_TEAL",
]
