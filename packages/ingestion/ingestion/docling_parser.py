"""Optional Docling backend (IBM Docling, MIT) — a license-clean local Tier-2 PDF parser.

Docling is a heavy optional dependency (PyTorch + models). It is **lazy-imported** and only used when
installed; otherwise the cascade skips it. The mapping is defensive (best-effort) so minor Docling API
differences degrade to a whole-document markdown text asset rather than failing.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Optional

from slide_ir import EvidenceAsset

from .models import IngestResult, add_table, is_low_quality_table
from .models import TableBlock  # noqa: E402  (kept explicit for clarity)


def docling_available() -> bool:
    return importlib.util.find_spec("docling") is not None


def ingest_pdf_docling(path: str | Path, workspace: Optional[str | Path] = None) -> IngestResult:
    """Parse a PDF with Docling into the Evidence Pool. Raises if Docling isn't installed."""
    from docling.document_converter import DocumentConverter  # lazy / optional

    path = Path(path)
    result = IngestResult()
    doc = DocumentConverter().convert(str(path)).document

    pages: dict[int, list[str]] = {}
    try:
        for item in getattr(doc, "texts", []) or []:
            txt = (getattr(item, "text", "") or "").strip()
            if not txt:
                continue
            prov = getattr(item, "prov", None)
            page = int(prov[0].page_no) if prov else 1
            label = str(getattr(item, "label", "")).lower()
            prefix = "# " if ("header" in label or "title" in label) else ""
            pages.setdefault(page, []).append(prefix + txt)
    except Exception:
        pages = {}

    if pages:
        for page in sorted(pages):
            result.assets.append(
                EvidenceAsset(
                    asset_id=f"{path.stem}:p{page}",
                    kind="section_text",
                    content_ref="\n".join(pages[page]),
                    source=path.name,
                    locator={"page": page},
                )
            )
    else:  # fallback: whole-document markdown as one text asset
        md = ""
        try:
            md = doc.export_to_markdown()
        except Exception:
            md = ""
        if md.strip():
            result.assets.append(
                EvidenceAsset(asset_id=f"{path.stem}:full", kind="section_text", content_ref=md, source=path.name)
            )

    for ti, table in enumerate(getattr(doc, "tables", []) or []):
        try:
            df = table.export_to_dataframe()
            cols = [str(c) for c in df.columns]
            rows = [[("" if x is None else str(x)) for x in row] for row in df.values.tolist()]
            tb = TableBlock(columns=cols or ["col1"], rows=rows, needs_human_check=True)
            if not is_low_quality_table(tb):
                add_table(result, tb, asset_id=f"{path.stem}:t{ti}", source=path.name, locator={})
        except Exception:
            continue

    if workspace is not None:
        ws = Path(workspace)
        ws.mkdir(parents=True, exist_ok=True)
        for pi, pic in enumerate(getattr(doc, "pictures", []) or []):
            try:
                img = pic.get_image(doc)
                if img is None:
                    continue
                dst = ws / f"{path.stem}_docling_fig{pi + 1}.png"
                img.save(str(dst))
                result.assets.append(
                    EvidenceAsset(
                        asset_id=f"{path.stem}:fig{pi + 1}", kind="figure", content_ref=str(dst), source=path.name
                    )
                )
            except Exception:
                continue

    return result
