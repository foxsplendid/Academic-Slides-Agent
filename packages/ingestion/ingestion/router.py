"""Route each input to the right extractor by file extension; combine multiple inputs."""

from __future__ import annotations

from pathlib import Path

from slide_ir import EvidenceAsset

from .models import IngestResult
from .pdf import ingest_pdf
from .spreadsheet import ingest_csv, ingest_xlsx

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def ingest_path(path: str | Path) -> IngestResult:
    path = Path(path)
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return ingest_xlsx(path)
    if ext == ".csv":
        return ingest_csv(path)
    if ext == ".pdf":
        return ingest_pdf(path)
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


def ingest(*paths: str | Path) -> IngestResult:
    result = IngestResult()
    for path in paths:
        result.merge(ingest_path(Path(path)))
    return result
