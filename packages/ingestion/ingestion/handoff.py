"""Ingest a Scriptorium `handoff/1.x` package (Steward `pick` output) into the Evidence Pool.

A handoff package is a directory holding one or more papers' PDFs + a `meta.json` sidecar (contract
`handoff/1.x`, owned by the scriptorium-spec repo — the coordination point). We read the curated
bibliographic metadata, ingest each paper's PDF through the standard PDF cascade (MinerU → Docling →
pdfplumber, cached), and inject `title/authors/year/doi` as provenance so the deck can state
"本报告基于 …". Backward-compatible with the single-paper `handoff/1.0` shape (top-level fields = one
paper); `handoff/1.1` adds `report_type` + a `papers[]` array. Stdlib only — no new dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from slide_ir import EvidenceAsset

from .models import IngestResult

_PAPER_FIELDS = ("title", "authors", "year", "doi", "tldr", "abstract", "pdfFilename", "folders")


def is_handoff_dir(path: str | Path) -> bool:
    """True for a directory carrying a `meta.json` whose `schema_version` starts with `handoff/`."""
    p = Path(path)
    meta = p / "meta.json"
    if not (p.is_dir() and meta.is_file()):
        return False
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        return False
    return isinstance(data, dict) and str(data.get("schema_version", "")).startswith("handoff/")


def _papers(meta: dict) -> list[dict]:
    """Normalize a meta.json to a list of per-paper dicts: `papers[]` (1.1) when present, else the
    top-level fields as a single paper (1.0)."""
    papers = meta.get("papers")
    if isinstance(papers, list):
        kept = [p for p in papers if isinstance(p, dict)]
        if kept:
            return kept
    return [{k: meta.get(k) for k in _PAPER_FIELDS}]  # 1.0: top-level fields ARE the one paper


def _fmt_authors(authors) -> str:
    if isinstance(authors, list):
        names = [str(a).strip() for a in authors if str(a).strip()]
    elif authors:
        names = [str(authors).strip()]
    else:
        names = []
    if not names:
        return ""
    return ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")


def _citation(paper: dict) -> str:
    """One-line human citation: `Title — Authors (Year). doi:...` (omitting absent fields)."""
    bits = [(paper.get("title") or "").strip() or "(无标题)"]
    authors = _fmt_authors(paper.get("authors"))
    year = (paper.get("year") or "").strip()
    tail = [t for t in (authors, f"({year})" if year else "") if t]
    if tail:
        bits.append("— " + " ".join(tail))
    line = " ".join(bits)
    doi = (paper.get("doi") or "").strip()
    return f"{line}. doi:{doi}" if doi else line


def _basis_asset(meta: dict, papers: list[dict], report_type: str) -> EvidenceAsset:
    """The "本报告基于 …" hook: a section_text asset the planner reads to cite the report's source(s)."""
    key = str(meta.get("key") or "").strip()
    if len(papers) == 1:
        body = f"本报告基于:{_citation(papers[0])}"
        tldr = (papers[0].get("tldr") or "").strip()
        if tldr:
            body += f"\n一句话:{tldr}"
    else:
        label = "实验报告" if report_type == "experiment" else "综述报告"
        lines = [f"本报告({label})综合以下 {len(papers)} 篇文献:"]
        lines += [f"{i}) {_citation(p)}" for i, p in enumerate(papers, start=1)]
        body = "\n".join(lines)
    locator = {
        "report_type": report_type,
        "handoff_key": key,
        "papers": [
            {
                "title": (p.get("title") or "").strip(),
                "year": (p.get("year") or "").strip(),
                "doi": (p.get("doi") or "").strip(),
            }
            for p in papers
        ],
    }
    return EvidenceAsset(
        asset_id="report_basis",
        kind="section_text",
        content_ref=body,
        source=f"handoff:{key}" if key else "handoff",
        locator=locator,
    )


def _meta_asset(paper: dict, *, asset_id: str, source: str) -> EvidenceAsset:
    """Per-paper bibliographic metadata as section_text evidence (factual, not model-generated)."""
    parts = [f"标题:{(paper.get('title') or '').strip()}"]
    for label, value in (
        ("作者", _fmt_authors(paper.get("authors"))),
        ("年份", (paper.get("year") or "").strip()),
        ("DOI", (paper.get("doi") or "").strip()),
        ("一句话主旨", (paper.get("tldr") or "").strip()),
        ("摘要", (paper.get("abstract") or "").strip()),
    ):
        if value:
            parts.append(f"{label}:{value}")
    locator = {
        "title": (paper.get("title") or "").strip(),
        "authors": [str(a) for a in paper["authors"]] if isinstance(paper.get("authors"), list) else [],
        "year": (paper.get("year") or "").strip(),
        "doi": (paper.get("doi") or "").strip(),
    }
    return EvidenceAsset(asset_id=asset_id, kind="section_text", content_ref="\n".join(parts), source=source, locator=locator)


def _namespace(result: IngestResult, prefix: str) -> None:
    """Prefix every asset id so multiple papers in one package never collide on the compile resolver
    (`pdf.py` keys ids off the filename stem; generic/duplicate names would otherwise clash)."""
    for asset in result.assets:
        asset.asset_id = f"{prefix}{asset.asset_id}"


def ingest_handoff(
    path: str | Path,
    *,
    workspace: Optional[str | Path] = None,
    cache_dir: Optional[str | Path] = None,
) -> IngestResult:
    """Ingest a handoff directory. Best-effort: a malformed package warns rather than raises."""
    from .router import ingest_path  # lazy import to avoid a cycle

    p = Path(path)
    result = IngestResult()
    try:
        meta = json.loads((p / "meta.json").read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            raise ValueError("meta.json is not a JSON object")
    except Exception as err:
        result.warnings.append(f"取件包 meta.json 无法解析:{err}")
        return result

    sv = str(meta.get("schema_version", ""))
    if not sv.startswith("handoff/1."):
        result.warnings.append(f"未知的取件包契约版本 {sv!r},按 handoff/1.x 尽力解析。")
    report_type = str(meta.get("report_type") or "literature").strip().lower()
    if report_type not in ("literature", "experiment"):
        report_type = "literature"
    papers = _papers(meta)
    key = str(meta.get("key") or "").strip()

    result.assets.append(_basis_asset(meta, papers, report_type))

    multi = len(papers) > 1
    for idx, paper in enumerate(papers, start=1):
        prefix = f"p{idx}_" if multi else ""
        pdf_name = (paper.get("pdfFilename") or "").strip()
        source = pdf_name or (f"handoff:{key}" if key else "handoff")
        result.assets.append(_meta_asset(paper, asset_id=f"{prefix}meta", source=source))
        pdf_path = p / pdf_name if pdf_name else None
        if pdf_path is not None and pdf_path.is_file():
            sub = ingest_path(pdf_path, workspace=workspace, cache_dir=cache_dir)
            if multi:
                _namespace(sub, prefix)
            result.merge(sub)
        elif pdf_name:
            result.warnings.append(f"取件包缺少 PDF:{pdf_name}")
    return result
