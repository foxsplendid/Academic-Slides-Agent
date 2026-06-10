"""Tabler icon -> tinted PNG, via the Node/resvg sidecar (arms-length, cached).

Icons come from the MIT-licensed upstream `@tabler/icons` npm package (installed alongside the
MathJax sidecar). `ICON_WHITELIST` is the closed vocabulary the planner may use — unknown names are
skipped silently, so a hallucinated icon can never break a render (omit-over-decorate policy).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

_SIDECAR_DIR = Path(__file__).resolve().parent.parent / "node"
_ICON_JS = _SIDECAR_DIR / "icon_render.js"
_ICONS_DIR = _SIDECAR_DIR / "node_modules" / "@tabler" / "icons" / "icons" / "outline"

# Closed vocabulary for academic decks (concept-bearing only; no decorative noise).
ICON_WHITELIST = (
    "database", "chart-bar", "chart-line", "chart-dots", "chart-pie", "trending-up", "trending-down",
    "flask", "microscope", "atom", "math-function", "calculator", "binary-tree", "network",
    "cpu", "robot", "settings", "target", "bulb", "alert-triangle", "circle-check", "x",
    "arrow-right", "clock", "calendar", "map-pin", "world", "mountain", "droplet", "flame",
    "wind", "snowflake", "book", "file-text", "table", "photo", "search", "scale",
    "ruler", "thermometer", "gauge", "refresh", "layers-intersect", "stack-2", "school", "award",
)


class IconRenderer:
    """Render a whitelisted icon to a tinted PNG; returns None on any failure (fail open)."""

    def __init__(self, out_dir: str | Path | None = None, *, node: str = "node", timeout: int = 10) -> None:
        base = Path(out_dir) if out_dir else Path(tempfile.gettempdir()) / "asa_icons"
        self.out_dir = base.resolve()  # the sidecar runs with a different cwd — keep paths absolute
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.node = node
        self.timeout = timeout

    @staticmethod
    def available(node: str = "node") -> bool:
        return bool(shutil.which(node)) and _ICON_JS.is_file() and _ICONS_DIR.is_dir()

    def render(self, name: str, color_hex: str = "#333333", size_px: int = 64) -> Optional[Path]:
        # Open vocabulary: any installed Tabler outline icon renders; unknown names fail open. The
        # static ICON_WHITELIST remains only as prompt examples / corpus-absent fallback.
        safe = "".join(ch for ch in name if ch.isalnum() or ch == "-")
        if not safe or not (_ICONS_DIR / f"{safe}.svg").is_file():
            return None
        name = safe
        key = hashlib.sha1(f"{name}|{color_hex}|{size_px}".encode()).hexdigest()[:14]
        out = self.out_dir / f"icon_{key}.png"
        if out.is_file():
            return out
        try:
            proc = subprocess.run(
                [self.node, str(_ICON_JS), name, color_hex, str(size_px), str(out)],
                capture_output=True,
                timeout=self.timeout,
                cwd=str(_SIDECAR_DIR),
            )
            return out if proc.returncode == 0 and out.is_file() else None
        except Exception:
            return None


def default_icon_renderer(out_dir: str | Path | None = None) -> Optional[IconRenderer]:
    """An IconRenderer when the sidecar + icon corpus are present, else None (icons just skip)."""
    return IconRenderer(out_dir) if IconRenderer.available() else None
