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
MAX_BULLETS = 9
MAX_BULLET_CHARS = 200
MAX_TABLE_COLS = 6
MAX_TABLE_ROWS = 12
MIN_TITLE_SIM = 0.85  # >= this normalized-title similarity counts two slides as near-duplicates
MAX_STAT_ITEMS = 4  # more cards than fit one row -> repair finding (schema no longer hard-rejects)
MAX_BLOCKS_PER_SLIDE = 3  # vertical stacking beyond this is always cramped (figure_grid exempt)
_HEAVY_BLOCKS = {"figure", "chart", "diagram", "table"}
MAX_LAYOUT_RUN = 3  # > this many consecutive content slides sharing one layout reads stamped-out

# Layouts that carry no content blocks by design.
_STRUCTURAL_LAYOUTS = {LayoutType.TITLE, LayoutType.SECTION, LayoutType.ENDING}
_CONTENT_BLOCK_TYPES = {"bullets", "table", "figure", "chart", "diagram", "formula", "callout", "stat", "canvas"}


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


def _monotony_findings(slides: list[SlideIR]) -> list[str]:
    """Flag runs of >MAX_LAYOUT_RUN consecutive content slides with the SAME layout (visual monotony).
    Names a slide inside the run so the repair loop can relayout it (a structural divider or a TOC
    resets the run — the audience perceives runs within a section)."""
    out: list[str] = []
    run: list[SlideIR] = []

    def flush() -> None:
        if len(run) > MAX_LAYOUT_RUN:
            mid = run[len(run) // 2]
            out.append(  # advisory: reaches the human, does not consume the repair budget
                f"[建议] layout monotony around {mid.slide_id}: {len(run)} consecutive slides share "
                f"'{mid.layout_type.value}' — consider varying the composition"
            )

    for s in slides:
        if s.layout_type in _STRUCTURAL_LAYOUTS or s.layout_type is LayoutType.TOC:
            flush()
            run = []
        elif run and s.layout_type == run[-1].layout_type:
            run.append(s)
        else:
            flush()
            run = [s]
    flush()
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
        if s.layout_type == LayoutType.TOC and "bullets" not in kinds:
            findings.append(f"{tag}: layout 'toc' but no bullets block (the agenda items)")
        n_figs = sum(1 for b in s.blocks if b.type == "figure")
        if s.layout_type == LayoutType.FIGURE_GRID and 0 < n_figs < 2:
            findings.append(
                f"{tag}: figure_grid 不足两张图({n_figs} 张)——改用 figure_caption/figure_left"
            )
        # sparseness: a content page that says almost nothing wastes a slide
        n_bullets = sum(len(b.items) for b in s.blocks if b.type == "bullets")
        heavies = sum(1 for b in s.blocks if b.type in _HEAVY_BLOCKS)
        if (
            s.layout_type not in (LayoutType.TOC, LayoutType.BIG_FIGURE, LayoutType.CANVAS)
            and s.layout_type not in _STRUCTURAL_LAYOUTS
            and s.blocks
            and heavies == 0
            and n_bullets <= 2
        ):
            findings.append(
                f"{tag}: 内容过少(无图表且要点≤2 条)——依据证据充实到 4 条以上有实质的要点,或该页并入相邻页"
            )
        # density: an overloaded page is always cramped; grids carry their figures by design
        if s.layout_type not in (LayoutType.FIGURE_GRID, LayoutType.TOC) and len(s.blocks) > MAX_BLOCKS_PER_SLIDE:
            findings.append(
                f"{tag}: {len(s.blocks)} blocks on one slide (> {MAX_BLOCKS_PER_SLIDE}) — cramped; keep at most "
                f"one heavy visual + one callout/stat + bullets, fold the rest into the bullets"
            )
        heavy = [k for k in (b.type for b in s.blocks) if k in _HEAVY_BLOCKS]
        if s.layout_type not in (LayoutType.FIGURE_GRID, LayoutType.TWO_CONTENT) and len(heavy) > 1:
            findings.append(
                f"{tag}: {len(heavy)} heavy visual blocks ({'+'.join(heavy)}) stacked on one slide — keep one, "
                f"move or drop the others"
            )
        if s.layout_type == LayoutType.CANVAS:
            canvas_blocks = [b for b in s.blocks if b.type == "canvas"]
            if len(canvas_blocks) != 1:
                findings.append(f"{tag}: layout 'canvas' must carry exactly one canvas block")
            else:
                try:
                    from pptx_compiler import lint_canvas_svg, validate_canvas_svg

                    issues = validate_canvas_svg(canvas_blocks[0].svg) or lint_canvas_svg(canvas_blocks[0].svg)
                    for issue in issues:
                        findings.append(f"{tag}: {issue}")
                except Exception:
                    pass

        # Per-block overflow / reference checks.
        for b in s.blocks:
            if b.type == "bullets":
                texts = [it if isinstance(it, str) else it.text for it in b.items]
                n_lines = sum(1 + (0 if isinstance(it, str) else len(it.children)) for it in b.items)
                if n_lines > MAX_BULLETS:
                    findings.append(
                        f"{tag}: bullet list too long ({n_lines} > {MAX_BULLETS} items)"
                    )
                for text in texts:
                    if len(text) > MAX_BULLET_CHARS:
                        findings.append(
                            f"{tag}: bullet item too long ({len(text)} > {MAX_BULLET_CHARS} chars)"
                        )
                        break
            elif b.type == "stat":
                if len(b.items) > MAX_STAT_ITEMS:
                    findings.append(f"{tag}: stat block has {len(b.items)} items (> {MAX_STAT_ITEMS} fit one row)")
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
    findings.extend(_monotony_findings(slides))
    findings.extend(_toc_section_findings(slides))
    return findings

def _toc_section_findings(slides) -> list[str]:
    """The agenda is a contract: every toc entry needs a matching section divider (and vice versa).
    Round-3 judges traced both the missing dividers and the mis-labeled footers to this mismatch."""
    toc_items: list[str] = []
    for s in slides:
        if s.layout_type is LayoutType.TOC:
            for b in s.blocks:
                if b.type == "bullets":
                    toc_items = [it if isinstance(it, str) else it.text for it in b.items]
            break
    sections = [s.title.strip() for s in slides if s.layout_type is LayoutType.SECTION]
    if not toc_items or not sections:
        return []
    out: list[str] = []
    if len(toc_items) != len(sections):
        out.append(
            f"目录列出 {len(toc_items)} 个章节但正文只有 {len(sections)} 个 section 分隔页——两者必须一一对应"
        )
    else:
        for t, sec in zip(toc_items, sections):
            if _norm_title(t) != _norm_title(sec):
                out.append(f"目录章节「{t}」与对应分隔页「{sec}」名称不一致")
    return out
