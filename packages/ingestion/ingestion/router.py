"""Route each input to the right extractor by file extension; combine multiple inputs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from slide_ir import EvidenceAsset

from .models import IngestResult
from .pdf import ingest_pdf
from .quality import assess_quality
from .spreadsheet import ingest_csv, ingest_xlsx

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
_PARSERS = ("mineru", "docling", "pdfplumber")


def _pdf_backends(forced: Optional[str], workspace: Optional[str | Path]) -> list[tuple]:
    """Ordered (name, fn) PDF backends. `forced` pins a single one; else a quality-gated cascade."""
    api_key = os.environ.get("MINERU_API_KEY")

    def mineru_fn(p: Path) -> IngestResult:
        from .mineru import ingest_pdf_mineru

        return ingest_pdf_mineru(
            p, api_key=api_key, workspace=workspace,
            api_url=os.environ.get("MINERU_API_URL", "https://mineru.net/api/v4"),
        )

    def docling_fn(p: Path) -> IngestResult:
        from .docling_parser import ingest_pdf_docling

        return ingest_pdf_docling(p, workspace=workspace)

    def plumber_fn(p: Path) -> IngestResult:
        return ingest_pdf(p, workspace=workspace)

    fns = {"mineru": mineru_fn, "docling": docling_fn, "pdfplumber": plumber_fn}
    if forced in fns:
        return [(forced, fns[forced])]

    order: list[tuple] = []
    if api_key and workspace is not None:
        order.append(("mineru", mineru_fn))
    from .docling_parser import docling_available

    if docling_available() and workspace is not None:
        order.append(("docling", docling_fn))
    order.append(("pdfplumber", plumber_fn))
    return order


def _ingest_pdf(
    path: Path, workspace: Optional[str | Path], cache_dir: Optional[str | Path] = None
) -> IngestResult:
    """Quality-gated cascade (cached). See `_ingest_pdf_uncached`."""
    if cache_dir is not None:
        from .cache import cached_pdf

        parser_key = os.environ.get("ASA_PDF_PARSER", "auto").lower()
        return cached_pdf(
            path,
            parser_key=parser_key,
            cache_dir=cache_dir,
            parse_fn=lambda p: _ingest_pdf_uncached(p, workspace),
        )
    return _ingest_pdf_uncached(path, workspace)


def _ingest_pdf_uncached(path: Path, workspace: Optional[str | Path]) -> IngestResult:
    """Quality-gated cascade: MinerU → Docling (if installed) → pdfplumber. Descend when a parse is
    inadequate (not only on exceptions); keep the best result if none is adequate.

    `ASA_PDF_PARSER` = auto (default) | mineru | docling | pdfplumber forces a single backend.
    """
    forced = os.environ.get("ASA_PDF_PARSER", "auto").lower()
    forced = forced if forced in _PARSERS else None
    backends = _pdf_backends(forced, workspace)
    first_name = backends[0][0] if backends else None

    best: Optional[IngestResult] = None
    best_score = -1
    for name, fn in backends:
        try:
            res = fn(path)
        except Exception:
            continue
        q = assess_quality(res)
        if q["adequate"]:
            if name != first_name:
                res.warnings.append(f"已自动降级到 {name} 解析(前一解析器结果过差)。")
            return res
        if q["score"] > best_score:
            best, best_score = res, q["score"]
    if best is None:
        return IngestResult(warnings=["所有解析器都未能从该 PDF 提取到内容。"])
    best.warnings.extend(assess_quality(best)["warnings"])
    return best


def ingest_path(
    path: str | Path,
    *,
    workspace: Optional[str | Path] = None,
    cache_dir: Optional[str | Path] = None,
) -> IngestResult:
    path = Path(path)
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        return ingest_xlsx(path)
    if ext == ".csv":
        return ingest_csv(path)
    if ext == ".pdf":
        return _ingest_pdf(path, workspace, cache_dir)
    if ext == ".zip":
        from .archive import ingest_zip

        return ingest_zip(path, workspace=workspace, cache_dir=cache_dir)
    if ext in _IMAGE_EXT:
        result = IngestResult()
        result.assets.append(
            EvidenceAsset(asset_id=path.stem, kind="figure", content_ref=str(path), source=path.name, locator={})
        )
        return result
    return IngestResult()  # unknown type -> skipped (no raise)


def ingest(
    *paths: str | Path,
    workspace: Optional[str | Path] = None,
    cache_dir: Optional[str | Path] = None,
) -> IngestResult:
    result = IngestResult()
    for path in paths:
        result.merge(ingest_path(Path(path), workspace=workspace, cache_dir=cache_dir))
    return result
