"""Route each input to the right extractor by file extension; combine multiple inputs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from slide_ir import EvidenceAsset

from .models import IngestResult
from .pdf import ingest_pdf
from .spreadsheet import ingest_csv, ingest_xlsx

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _ingest_pdf(path: Path, workspace: Optional[str | Path]) -> IngestResult:
    """Use the MinerU cloud backend when configured + a workspace is available; else pdfplumber.

    `ASA_PDF_PARSER` = auto (default) | mineru | pdfplumber. MinerU failures fall back gracefully.
    """
    parser = os.environ.get("ASA_PDF_PARSER", "auto").lower()
    api_key = os.environ.get("MINERU_API_KEY")
    use_mineru = parser == "mineru" or (parser == "auto" and api_key and workspace is not None)
    if use_mineru and api_key and workspace is not None:
        from .mineru import ingest_pdf_mineru

        try:
            return ingest_pdf_mineru(
                path,
                api_key=api_key,
                workspace=workspace,
                api_url=os.environ.get("MINERU_API_URL", "https://mineru.net/api/v4"),
            )
        except Exception:
            if parser == "mineru":
                raise  # explicit request: surface the error
            # auto mode: degrade to the offline backend
    return ingest_pdf(path, workspace=workspace)


def ingest_path(path: str | Path, *, workspace: Optional[str | Path] = None) -> IngestResult:
    path = Path(path)
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return ingest_xlsx(path)
    if ext == ".csv":
        return ingest_csv(path)
    if ext == ".pdf":
        return _ingest_pdf(path, workspace)
    if ext == ".zip":
        from .archive import ingest_zip

        return ingest_zip(path)
    if ext in _IMAGE_EXT:
        result = IngestResult()
        result.assets.append(
            EvidenceAsset(asset_id=path.stem, kind="figure", content_ref=str(path), source=path.name, locator={})
        )
        return result
    return IngestResult()  # unknown type -> skipped (no raise)


def ingest(*paths: str | Path, workspace: Optional[str | Path] = None) -> IngestResult:
    result = IngestResult()
    for path in paths:
        result.merge(ingest_path(Path(path), workspace=workspace))
    return result
