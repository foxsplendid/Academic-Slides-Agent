"""High-fidelity LaTeX rendering via a MathJax(+mhchem) → resvg Node sidecar.

Covers full LaTeX math, **chemistry (mhchem)**, matrices, and alignment — things matplotlib mathtext
cannot. The sidecar is called as an **arms-length subprocess** (no linking), so MathJax (Apache-2.0)
and resvg (MPL-2.0) never touch our Apache Python code. Optional: requires Node.js + the sidecar's
`node_modules` (`npm install` in `packages/core/formula/node`). When unavailable, callers fall back to
the matplotlib/text renderer.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

_SIDECAR_DIR = Path(__file__).resolve().parent.parent / "node"
_SIDECAR_JS = _SIDECAR_DIR / "sidecar.js"


class MathJaxFormulaRenderer:
    """Render LaTeX to a cached PNG via the Node sidecar. `to_image` returns None on any failure."""

    def __init__(self, out_dir: str | Path | None = None, *, node: str = "node", timeout: int = 20) -> None:
        self.out_dir = Path(out_dir) if out_dir else Path(tempfile.gettempdir()) / "asa_formula_mj"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.node = node
        self.timeout = timeout

    @staticmethod
    def available(node: str = "node") -> bool:
        return bool(shutil.which(node)) and _SIDECAR_JS.is_file() and (_SIDECAR_DIR / "node_modules").is_dir()

    def _path_for(self, latex: str) -> Path:
        key = hashlib.sha1(f"mj|{latex}".encode("utf-8")).hexdigest()[:16]
        return self.out_dir / f"formula_{key}.png"

    def to_image(self, latex: str) -> Optional[Path]:
        out = self._path_for(latex)
        if out.exists():  # cache hit
            return out
        try:
            result = subprocess.run(
                [self.node, str(_SIDECAR_JS), latex, str(out)],
                cwd=str(_SIDECAR_DIR),
                capture_output=True,
                timeout=self.timeout,
            )
        except Exception:
            return None
        if result.returncode == 0 and out.exists() and out.stat().st_size > 0:
            return out
        out.unlink(missing_ok=True)
        return None
