"""pptx_compiler — deterministic Slide-IR -> native .pptx rendering."""

from .canvas import canvas_engine_available, validate_canvas_svg
from .compiler import compile_deck
from .formula_renderer import FormulaRenderer, NullFormulaRenderer
from .lint import lint_compiled_deck
from .style import ACADEMIC, MODERN_TEAL, StyleProfile, get_style, register_style
from .template_import import extract_style_from_pptx, import_template, profile_from_dict, profile_to_dict

__all__ = [
    "compile_deck",
    "validate_canvas_svg",
    "canvas_engine_available",
    "lint_compiled_deck",
    "FormulaRenderer",
    "NullFormulaRenderer",
    "StyleProfile",
    "get_style",
    "register_style",
    "import_template",
    "extract_style_from_pptx",
    "profile_to_dict",
    "profile_from_dict",
    "ACADEMIC",
    "MODERN_TEAL",
]
