"""Deterministic, AI-free deck critic (docs/SPEC.md §6: measure, then flag).

`critique_deck` inspects Slide-IR and returns human-readable findings. It is read-only: it never
edits content. The orchestration loop feeds the findings back to the planner LLM (or, after the retry
budget, to the human at the Hard-Stop). Keeping the critic deterministic makes runs reproducible and
free.
"""

from __future__ import annotations

import difflib
import re

from slide_ir import EvidenceAsset, LayoutType, SlideIR

# Thresholds — conservative on purpose; tune via a future OpenSpec change, not ad-hoc.
MAX_TITLE_CHARS = 100
MAX_BULLETS = 7
MAX_BULLET_CHARS = 200
MAX_TABLE_COLS = 6
MAX_TABLE_ROWS = 12
MIN_TITLE_SIM = 0.85  # >= this normalized-title similarity counts two slides as near-duplicates

# Layouts that carry no content blocks by design.
_STRUCTURAL_LAYOUTS = {LayoutType.TITLE, LayoutType.SECTION}
_CONTENT_BLOCK_TYPES = {"bullets", "table", "figure", "chart", "diagram", "formula"}


def _norm_title(t: str) -> str:
    # Unicode mode (no re.ASCII): \w keeps CJK, so only whitespace/ASCII punctuation is stripped.
    return re.sub(r"[\s\W_]+", "", (t or "").lower())


def _duplicate_title_findings(slides: list[SlideIR]) -> list[str]:
    """Flag near-duplicate content-slide titles. Worded WITHOUT the ``slide '<id>'`` token so the repair
    loop (which can only fix a slide in place, never delete one) does not loop on it — it reaches the
    human at the Hard-Stop instead. The deterministic ``_dedup_plans`` in deepen.py is the real fix."""
    content = [s for s in slides if s.layout_type not in _STRUCTURAL_LAYOUTS and s.title.strip()]
    out: list[str] = []
    for i in range(len(content)):
        ki = _norm_title(content[i].title)
        for j in range(i + 1, len(content)):
            kj = _norm_title(content[j].title)
            if ki == kj or difflib.SequenceMatcher(None, ki, kj).ratio() >= MIN_TITLE_SIM:
                out.append(
                    f"near-duplicate slides {content[i].slide_id} & {content[j].slide_id}: "
                    f"'{content[i].title}' ≈ '{content[j].title}' — consider removing one"
                )
    return out


def critique_deck(slides: list[SlideIR], evidence: list[EvidenceAsset]) -> list[str]:
    """Return a list of findings (empty == clean). Each finding names the slide and the defect."""
    asset_ids = {a.asset_id for a in evidence}
    findings: list[str] = []

    for s in slides:
        tag = f"slide '{s.slide_id}'"
        structural = s.layout_type in _STRUCTURAL_LAYOUTS

        # Title checks.
        if not structural and not s.title.strip():
            findings.append(f"{tag}: empty title on a content slide")
        if len(s.title) > MAX_TITLE_CHARS:
            findings.append(f"{tag}: title too long ({len(s.title)} > {MAX_TITLE_CHARS} chars)")

        # Empty content slide.
        if not structural and not s.blocks:
            findings.append(f"{tag}: content slide has no blocks")

        # Divider carrying content blocks — layout misselection (repair-routable: relayout in place).
        if structural and any(b.type in _CONTENT_BLOCK_TYPES for b in s.blocks):
            findings.append(
                f"{tag}: layout '{s.layout_type.value}' is a divider but carries content blocks; "
                "relayout to bullet_evidence"
            )

        kinds = {b.type for b in s.blocks}

        # Layout/block consistency.
        if s.layout_type == LayoutType.FORMULA_BANNER and "formula" not in kinds:
            findings.append(f"{tag}: layout 'formula_banner' but no formula block")
        if s.layout_type == LayoutType.TWO_COLUMN_TABLE and not (kinds & {"table", "chart", "diagram"}):
            findings.append(f"{tag}: layout 'two_column_table' but no table/chart/diagram block")
        if (
            s.layout_type
            in (LayoutType.FIGURE_CAPTION, LayoutType.FIGURE_LEFT, LayoutType.BIG_FIGURE, LayoutType.FIGURE_GRID)
            and "figure" not in kinds
        ):
            findings.append(f"{tag}: layout '{s.layout_type.value}' but no figure block")

        # Per-block overflow / reference checks.
        for b in s.blocks:
            if b.type == "bullets":
                if len(b.items) > MAX_BULLETS:
                    findings.append(
                        f"{tag}: bullet list too long ({len(b.items)} > {MAX_BULLETS} items)"
                    )
                for item in b.items:
                    if len(item) > MAX_BULLET_CHARS:
                        findings.append(
                            f"{tag}: bullet item too long ({len(item)} > {MAX_BULLET_CHARS} chars)"
                        )
                        break
            elif b.type == "table":
                if len(b.columns) > MAX_TABLE_COLS:
                    findings.append(
                        f"{tag}: table too wide ({len(b.columns)} > {MAX_TABLE_COLS} columns)"
                    )
                if len(b.rows) > MAX_TABLE_ROWS:
                    findings.append(
                        f"{tag}: table too tall ({len(b.rows)} > {MAX_TABLE_ROWS} rows)"
                    )
            elif b.type == "figure":
                if b.asset_id not in asset_ids:
                    findings.append(
                        f"{tag}: figure references unknown asset_id '{b.asset_id}'"
                    )
            elif b.type == "diagram":
                node_ids = {nd.id for nd in b.nodes}
                for e in b.edges:
                    if e.source not in node_ids or e.target not in node_ids:
                        findings.append(
                            f"{tag}: diagram edge references undefined node "
                            f"('{e.source}'->'{e.target}')"
                        )
                        break

    findings.extend(_duplicate_title_findings(slides))
    return findings
