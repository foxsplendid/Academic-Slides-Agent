"""Vendored-code config shim (local modification, see README): replaces backend.config.

Canvas formats are copied verbatim from the MIT snapshot's backend/config.py; the icons
directory comes from ASA_SVG_ICONS_DIR (unset -> icon embedding is skipped by callers).
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

CANVAS_FORMATS = {
    "ppt169": {"name": "PPT 16:9", "width": 1280, "height": 720, "viewbox": "0 0 1280 720", "ratio": "16:9"},
    "ppt43": {"name": "PPT 4:3", "width": 1024, "height": 768, "viewbox": "0 0 1024 768", "ratio": "4:3"},
}

_icons = os.environ.get("ASA_SVG_ICONS_DIR")
settings = SimpleNamespace(icons_dir=Path(_icons) if _icons else None)
