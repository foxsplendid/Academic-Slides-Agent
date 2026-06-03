"""Best-effort PDF ingestion via pdfplumber (pdfminer.six, MIT) — NOT PyMuPDF (AGPL).

Page text becomes a `section_text` asset; detected tables become best-effort TableBlocks
flagged `needs_human_check`.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from slide_ir import EvidenceAsset

from .models import IngestResult, add_table, rows_to_table


def ingest_pdf(path: str | Path) -> IngestResult:
    path = Path(path)
    result = IngestResult()
    with pdfplumber.open(str(path)) as pdf:
        for pageno, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
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
                if table is not None:
                    add_table(
                        result,
                        table,
                        asset_id=f"{path.stem}:p{pageno}:t{ti}",
                        source=path.name,
                        locator={"page": pageno},
                    )
    return result
