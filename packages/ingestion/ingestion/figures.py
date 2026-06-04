"""Caption-anchored figure rendering.

The hard-science figures we target are vector charts (no embedded raster to pull out), so we *render*
the region above each ``Fig. N`` caption with pypdfium2 (PDFium = BSD; never PyMuPDF/AGPL). Best-effort
by design: the region is the caption's horizontal band, from the body-prose line just above it down to
the caption.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from slide_ir import EvidenceAsset

_CAPTION = re.compile(r"^(?:Fig\.?|Figure)\s*\.?\s*(\d+)", re.IGNORECASE)
_RENDER_DPI = 200
_MIN_REGION_PT = 40.0  # skip implausibly thin regions


def _region_top(lines: list[dict], cap_line: dict, band: tuple[float, float], page_height: float) -> float:
    """Top of the figure region: the bottom of the nearest body-prose line above the caption, but
    bounded so we capture a real figure. Lines within 60pt of the caption are ignored (figure-internal
    labels or a wrapped caption line); the region is floored at ~60% of page height so a figure with no
    prose directly above it (top of a column) is still captured rather than clipped to nothing."""
    bx0, bx1 = band
    bw = bx1 - bx0
    cap_top = cap_line["top"]
    prose_floor = 0.0
    for ln in lines:
        if ln is cap_line or ln["bottom"] > cap_top - 90:
            continue  # only clearly-above lines (skip the figure-internal / caption-wrap band)
        overlap = min(bx1, ln["x1"]) - max(bx0, ln["x0"])
        if overlap < 0.3 * bw:
            continue  # not in the figure's column
        text = ln["text"].strip()
        is_prose = (ln["x1"] - ln["x0"]) > 0.6 * bw and len(text) > 40 and not _CAPTION.match(text)
        if is_prose:
            prose_floor = max(prose_floor, ln["bottom"])
    bounded = max(0.0, cap_top - 0.60 * page_height)
    return max(prose_floor, bounded)


def extract_figures(path: str | Path, workspace: str | Path) -> list[EvidenceAsset]:
    """Render caption-anchored figures from ``path`` into ``workspace``; return figure assets."""
    import pypdfium2 as pdfium  # lazy: heavy native dep

    path = Path(path)
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    assets: list[EvidenceAsset] = []

    doc = pdfium.PdfDocument(str(path))
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf.pages):
                if page.rotation:  # rotated pages would misalign the crop; skip for v1
                    continue
                lines = page.extract_text_lines()
                for ln in lines:
                    m = _CAPTION.match(ln["text"].strip())
                    if not m:
                        continue
                    fig_no = m.group(1)
                    pad = 8.0
                    band = (max(0.0, ln["x0"] - pad), min(page.width, ln["x1"] + pad))
                    region_top = _region_top(lines, ln, (ln["x0"], ln["x1"]), page.height)
                    region_bottom = ln["top"] - 2.0
                    if region_bottom - region_top < _MIN_REGION_PT:
                        continue
                    png = _render_region(
                        doc, page_index, (band[0], region_top, band[1], region_bottom),
                        page.height, workspace, f"{path.stem}_fig{fig_no}_p{page_index + 1}",
                    )
                    if png is None:
                        continue
                    assets.append(
                        EvidenceAsset(
                            asset_id=f"{path.stem}:fig{fig_no}:p{page_index + 1}",
                            kind="figure",
                            content_ref=str(png),
                            source=path.name,
                            locator={"page": page_index + 1, "caption": ln["text"].strip()[:200]},
                        )
                    )
    finally:
        doc.close()
    return assets


def _render_region(doc, page_index, bbox, page_height, workspace, stem) -> Path | None:
    """Render a PDF-point bbox (top-left origin) on a page to a cropped PNG; None on failure."""
    try:
        scale = _RENDER_DPI / 72.0
        pil = doc[page_index].render(scale=scale).to_pil()
        x0, top, x1, bottom = bbox
        crop = pil.crop((int(x0 * scale), int(top * scale), int(x1 * scale), int(bottom * scale)))
        if crop.width < 8 or crop.height < 8:
            return None
        out = Path(workspace) / f"{stem}.png"
        crop.save(str(out))
        return out
    except Exception:
        return None
