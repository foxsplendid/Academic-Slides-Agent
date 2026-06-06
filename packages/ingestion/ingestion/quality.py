"""Parse-quality assessment — decides whether a parse is good enough or we should descend a backend.

Used by the quality-gated PDF cascade (router) and surfaced to the user so a thin/scanned PDF is
caught *before* spending LLM calls.
"""

from __future__ import annotations

from .models import IngestResult

MIN_TEXT_CHARS = 800  # below this, a parse is likely a scan or a failure


def assess_quality(result: IngestResult) -> dict:
    """Score a parse and decide adequacy. Pure (reads the result's assets/tables)."""
    text_chars = sum(
        len(a.content_ref or "") for a in result.assets if a.kind == "section_text"
    )
    text_pages = sum(1 for a in result.assets if a.kind == "section_text")
    figures = sum(1 for a in result.assets if a.kind == "figure")
    tables = len(result.tables)
    adequate = text_chars >= MIN_TEXT_CHARS and text_pages >= 1

    warnings: list[str] = []
    if not adequate:
        warnings.append(
            f"解析得到的正文很少({text_chars} 字 / {text_pages} 页),可能是扫描件、加密 PDF 或解析失败;"
            "建议确认源文件或更换解析器。"
        )
    return {
        "text_chars": text_chars,
        "text_pages": text_pages,
        "figures": figures,
        "tables": tables,
        "adequate": adequate,
        "score": text_chars,  # ranking key when no backend is adequate
        "warnings": warnings,
    }
