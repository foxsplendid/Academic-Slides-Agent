"""pptx_compiler — deterministic Slide-IR -> native .pptx rendering."""

from .compiler import compile_deck
from .formula_renderer import FormulaRenderer, NullFormulaRenderer

__all__ = ["compile_deck", "FormulaRenderer", "NullFormulaRenderer"]
