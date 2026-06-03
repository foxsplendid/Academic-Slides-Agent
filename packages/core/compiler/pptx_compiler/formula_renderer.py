"""Pluggable formula rendering.

The compiler asks a `FormulaRenderer` for an image of a LaTeX string. When none is available
it falls back to placing the LaTeX as editable text, so the compiler never hard-fails on
formulas. The real LaTeX->SVG renderer arrives in the `add-formula-svg` change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class FormulaRenderer(Protocol):
    def to_image(self, latex: str) -> Optional[Path]:
        """Return a path to a rendered image of `latex`, or None to fall back to text."""
        ...


class NullFormulaRenderer:
    """MVP renderer: produces no image, so the compiler falls back to LaTeX-as-text."""

    def to_image(self, latex: str) -> Optional[Path]:  # noqa: D102
        return None
