"""Best-effort PDF ingestion via pdfplumber (pdfminer.six, MIT) — NOT PyMuPDF (AGPL).

Page text becomes a `section_text` asset (two-column aware); detected tables become best-effort
TableBlocks flagged `needs_human_check`, after low-quality tables are filtered out.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pdfplumber

from slide_ir import EvidenceAsset

from .figures import extract_figures
from .models import IngestResult, add_table, is_low_quality_table, rows_to_table


def _extract_page_text(page) -> str:
    """Two-column-aware extraction: if a clear central gutter splits the words into left/right
    blocks, read each column separately (so columns are not interleaved); else extract normally."""
    try:
        words = page.extract_words()
    except Exception:
        words = []
    if words:
        mid = page.width / 2.0
        crossing = sum(1 for w in words if w["x0"] < mid < w["x1"])
        left = [w for w in words if w["x1"] <= mid]
        right = [w for w in words if w["x0"] >= mid]
        two_col = crossing <= 0.04 * len(words) and min(len(left), len(right)) >= 0.2 * len(words)
        if two_col:
            lt = page.crop((0, 0, mid, page.height)).extract_text() or ""
            rt = page.crop((mid, 0, page.width, page.height)).extract_text() or ""
            return (lt.strip() + "\n" + rt.strip()).strip()
    return (page.extract_text() or "").strip()


def ingest_pdf(path: str | Path, *, workspace: Optional[str | Path] = None) -> IngestResult:
    path = Path(path)
    result = IngestResult()
    with pdfplumber.open(str(path)) as pdf:
        for pageno, page in enumerate(pdf.pages, start=1):
            text = _extract_page_text(page)
            if text:
                result.assets.append(
                    EvidenceAsset(
                        asset_id=f"{path.stem}:p{pageno}",
                        kind="section_text",
                        content_ref=text,
                        source=path.name,
                        locator={"page": pageno},
                    )
                )
            for ti, raw in enumerate(page.extract_tables() or []):
                table = rows_to_table(
                    raw,
                    caption=f"{path.name} · p{pageno} · table{ti + 1}",
                    needs_human_check=True,
                )
                if table is None or is_low_quality_table(table):
                    continue  # skip noise so it never reaches the planner
                add_table(
                    result,
                    table,
                    asset_id=f"{path.stem}:p{pageno}:t{ti}",
                    source=path.name,
                    locator={"page": pageno},
                )
    if workspace is not None:  # render caption-anchored figures into the workspace
        result.assets.extend(extract_figures(path, workspace))
    return result
