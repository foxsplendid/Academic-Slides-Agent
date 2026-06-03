"""Render LaTeX math to a high-DPI PNG via matplotlib's mathtext (pure-Python, BSD).

Implements the compiler's ``FormulaRenderer`` protocol structurally:
``to_image(latex) -> Path | None``. Returns ``None`` for expressions mathtext cannot parse, so
the compiler falls back to editable text. A higher-fidelity MathJax/SVG backend can later
replace this behind the same interface (docs/SPEC.md §6.2).
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # headless; no display needed

import matplotlib.pyplot as plt  # noqa: E402  (must follow backend selection)


class MatplotlibFormulaRenderer:
    """Render LaTeX math to a cached PNG. In-process, no network, no Node."""

    def __init__(
        self,
        out_dir: str | Path | None = None,
        *,
        dpi: int = 300,
        color: str = "#1D1D1F",
    ) -> None:
        self.out_dir = Path(out_dir) if out_dir else Path(tempfile.gettempdir()) / "asa_formula"
        self.dpi = dpi
        self.color = color
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, latex: str) -> Path:
        key = hashlib.sha1(f"{self.dpi}|{self.color}|{latex}".encode("utf-8")).hexdigest()[:16]
        return self.out_dir / f"formula_{key}.png"

    def to_image(self, latex: str) -> Optional[Path]:
        out = self._path_for(latex)
        if out.exists():  # cache hit — render once, reuse
            return out

        fig = plt.figure(figsize=(0.1, 0.1))
        try:
            fig.text(0.0, 0.0, f"${latex}$", fontsize=24, color=self.color)
            fig.savefig(out, dpi=self.dpi, bbox_inches="tight", pad_inches=0.05, transparent=True)
        except Exception:
            # mathtext could not parse this expression -> caller falls back to text
            out.unlink(missing_ok=True)
            return None
        finally:
            plt.close(fig)
        return out
