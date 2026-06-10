"""Deterministic Slide-IR -> native .pptx compiler.

Pure rendering (no AI): same Deck in -> same pptx structure out. Uses explicit positioning so
it is template-agnostic; placeholder/Manifest binding is a later change (add-template-mapper).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from slide_ir import (
    BulletBlock,
    CalloutBlock,
    ChartBlock,
    Deck,
    DiagramBlock,
    FigureBlock,
    FormulaBlock,
    LayoutType,
    SlideIR,
    StatBlock,
    TableBlock,
)

from . import blocks as _blocks
from .formula_renderer import FormulaRenderer, NullFormulaRenderer
from .style import ACADEMIC, StyleProfile, get_style

_DEFAULT_STYLE = ACADEMIC

_MARGIN = Inches(0.5)
_CENTERED = (LayoutType.TITLE, LayoutType.SECTION, LayoutType.ENDING)
# Figures dominate; tables/formulas need room; bullets are compact. Used for weighted region heights.
_BLOCK_WEIGHT = {
    "figure": 3.2,
    "chart": 3.0,
    "diagram": 3.0,
    "table": 2.0,
    "formula": 1.6,
    "stat": 1.3,
    "bullets": 1.0,
    "callout": 0.7,
}
# Visual blocks otherwise crowd out co-located text; cap their combined height so bullets stay readable.
_VISUAL_BLOCKS = {"figure", "chart", "diagram"}
_VISUAL_HEIGHT_CAP = 0.60


def _balanced_fractions(block_types: list[str]) -> list[float]:
    """Per-block height fractions from weights, with the combined figure/chart/diagram height capped at
    ``_VISUAL_HEIGHT_CAP`` when bullets co-exist (so co-located text keeps a readable share). A
    figure-only slide is unaffected (the cap only applies when bullets are present)."""
    weights = [_BLOCK_WEIGHT.get(t, 1.0) for t in block_types]
    fracs = [w / sum(weights) for w in weights]
    vis = [i for i, t in enumerate(block_types) if t in _VISUAL_BLOCKS]
    if vis and "bullets" in block_types:
        vis_sum = sum(fracs[i] for i in vis)
        if vis_sum > _VISUAL_HEIGHT_CAP:
            rest = [i for i in range(len(block_types)) if i not in vis]
            rest_sum = sum(fracs[i] for i in rest) or 1.0
            for i in vis:
                fracs[i] *= _VISUAL_HEIGHT_CAP / vis_sum
            for i in rest:
                fracs[i] *= (1 - _VISUAL_HEIGHT_CAP) / rest_sum
    return fracs


Region = tuple[int, int, int, int]


def _hsplit(content: Region, fracs: list[float], gap: int) -> list[Region]:
    left, top, w, h = content
    usable = w - gap * (len(fracs) - 1)
    out, x = [], left
    for f in fracs:
        cw = int(usable * f)
        out.append((x, top, cw, h))
        x += cw + gap
    return out


def _vsplit(content: Region, fracs: list[float], gap: int) -> list[Region]:
    left, top, w, h = content
    usable = h - gap * (len(fracs) - 1)
    out, y = [], top
    for f in fracs:
        ch = int(usable * f)
        out.append((left, y, w, ch))
        y += ch + gap
    return out


def _grid_regions(content: Region, n: int, gap: int) -> list[Region]:
    """2 -> side-by-side, 3 -> one row of three, 4 -> 2x2."""
    if n == 2:
        return _hsplit(content, [0.5, 0.5], gap)
    if n == 3:
        return _hsplit(content, [1 / 3] * 3, gap)
    rows = _vsplit(content, [0.5, 0.5], gap)
    return _hsplit(rows[0], [0.5, 0.5], gap) + _hsplit(rows[1], [0.5, 0.5], gap)


# Blocks that can anchor a side-by-side composition opposite a bullets column.
_MAJOR_BLOCKS = {"figure", "chart", "diagram", "table"}


def _regions_for(s: SlideIR, content: Region, gap: int) -> Optional[list[Region]]:
    """Multi-region template for this slide (one region per block, aligned to block order), or None
    for the vertical-stack fallback. Strict composition matching: a template only applies when the
    block composition fits it, so malformed plans degrade gracefully instead of breaking."""
    types = [b.type for b in s.blocks]
    n = len(types)
    lt = s.layout_type
    figs = [i for i, t in enumerate(types) if t == "figure"]
    buls = [i for i, t in enumerate(types) if t == "bullets"]

    # Explicit 50/50 two-up.
    if lt is LayoutType.TWO_CONTENT and n == 2:
        return _hsplit(content, [0.5, 0.5], gap)

    # One dominant figure (optionally a short text strip below).
    if lt is LayoutType.BIG_FIGURE and len(figs) == 1:
        if n == 1:
            return [content]
        if n == 2 and len(buls) == 1:
            fig_r, text_r = _vsplit(content, [0.74, 0.26], gap)
            out: list[Optional[Region]] = [None, None]
            out[figs[0]], out[buls[0]] = fig_r, text_r
            return out  # type: ignore[return-value]

    # Figure grid: 2-4 figures, optionally + one bullets strip at the bottom.
    if 2 <= len(figs) <= 4 and (len(figs) == n or (lt is LayoutType.FIGURE_GRID and n == len(figs) + 1 and len(buls) == 1)):
        if len(figs) == n:
            return _grid_regions(content, n, gap)
        top_r, bottom_r = _vsplit(content, [0.68, 0.32], gap)
        grid = iter(_grid_regions(top_r, len(figs), gap))
        return [next(grid) if t == "figure" else bottom_r for t in types]

    # Formula banner: formula band on top, support text below.
    if lt is LayoutType.FORMULA_BANNER and n == 2 and "formula" in types:
        f_i = types.index("formula")
        f_r, rest_r = _vsplit(content, [0.32, 0.68], gap)
        out = [None, None]
        out[f_i], out[1 - f_i] = f_r, rest_r
        return out  # type: ignore[return-value]

    # Side-by-side: one major block + one bullets column (the canonical academic composition).
    if n == 2 and len(buls) == 1 and types[1 - buls[0]] in _MAJOR_BLOCKS:
        major = 1 - buls[0]
        major_left = lt in (LayoutType.FIGURE_LEFT, LayoutType.TWO_COLUMN_TABLE)
        frac = 0.55 if types[major] == "table" else 0.58
        if major_left:
            major_r, text_r = _hsplit(content, [frac, 1 - frac], gap)
        else:
            text_r, major_r = _hsplit(content, [1 - frac, frac], gap)
        out = [None, None]
        out[major], out[buls[0]] = major_r, text_r
        return out  # type: ignore[return-value]

    return None  # vertical stack


def _blank_layout(prs):
    """Pick a content-free layout so we control positioning ourselves."""
    layouts = list(prs.slide_layouts)
    for layout in layouts:
        if "blank" in (layout.name or "").lower():
            return layout
    return min(layouts, key=lambda layout: len(list(layout.placeholders)))


def _render_block(slide, block, region, renderer: FormulaRenderer, asset_resolver=None, style=_DEFAULT_STYLE, icon_resolver=None):
    if isinstance(block, TableBlock):
        _blocks.render_table(slide, block, region, style)
    elif isinstance(block, BulletBlock):
        _blocks.render_bullets(slide, block, region, style)
    elif isinstance(block, FormulaBlock):
        _blocks.render_formula(slide, block, region, renderer)
    elif isinstance(block, FigureBlock):
        _blocks.render_figure(slide, block, region, asset_resolver, style)
    elif isinstance(block, ChartBlock):
        _blocks.render_chart(slide, block, region, style)
    elif isinstance(block, DiagramBlock):
        from .diagram import render_diagram

        render_diagram(slide, block, region, style)
    elif isinstance(block, CalloutBlock):
        _blocks.render_callout(slide, block, region, style, icon_resolver)
    elif isinstance(block, StatBlock):
        _blocks.render_stat(slide, block, region, style, icon_resolver)


def _accent_rect(slide, x: int, y: int, w: int, h: int, rgb) -> None:
    """A borderless solid rectangle — the only decor primitive the theme layer uses."""
    from pptx.enum.shapes import MSO_SHAPE

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb
    shape.line.fill.background()
    shape.shadow.inherit = False


def _add_page_number(slide, prs, style: StyleProfile, page_no: int) -> None:
    w, h = int(Inches(0.7)), int(Inches(0.32))
    box = slide.shapes.add_textbox(int(prs.slide_width) - w - int(Inches(0.25)), int(prs.slide_height) - h - int(Inches(0.12)), w, h)
    para = box.text_frame.paragraphs[0]
    para.alignment = PP_ALIGN.RIGHT
    run = para.add_run()
    run.text = str(page_no)
    run.font.size = Pt(10)
    run.font.name = style.latin_font
    run.font.color.rgb = style.muted_rgb


def _render_toc(slide, s: SlideIR, content: Region, style: StyleProfile) -> None:
    """Numbered agenda: accent number chips + section titles, generous spacing."""
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR

    items: list[str] = []
    for b in s.blocks:
        if isinstance(b, BulletBlock):
            items.extend(it if isinstance(it, str) else it.text for it in b.items)
    if not items:
        return
    left, top, width, height = content
    row_h = min(int(Inches(0.85)), height // max(len(items), 1))
    chip = int(Inches(0.5))
    for i, text in enumerate(items[:10]):
        y = top + i * row_h
        c = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, y + (row_h - chip) // 2, chip, chip)
        c.fill.solid()
        c.fill.fore_color.rgb = style.accent_rgb
        c.line.fill.background()
        c.shadow.inherit = False
        cp = c.text_frame.paragraphs[0]
        cp.alignment = PP_ALIGN.CENTER
        run = cp.add_run()
        run.text = str(i + 1)
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.name = style.latin_font
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        box = slide.shapes.add_textbox(left + chip + int(Inches(0.3)), y, width - chip - int(Inches(0.3)), row_h)
        box.text_frame.word_wrap = True
        box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = box.text_frame.paragraphs[0]
        _blocks.add_rich_text(para, text, size=Pt(style.body_pt + 4), bold=True, style=style, color=style.text_rgb)


def _render_slide(
    prs, slide, s: SlideIR, renderer: FormulaRenderer, asset_resolver=None, style=_DEFAULT_STYLE, page_no: int = 0, icon_resolver=None
) -> None:
    slide_w, slide_h = prs.slide_width, prs.slide_height
    content_left = int(_MARGIN)
    content_width = int(slide_w) - 2 * int(_MARGIN)

    if s.layout_type in _CENTERED:
        box = slide.shapes.add_textbox(content_left, int(Inches(2.2)), content_width, int(Inches(2.0)))
        box.text_frame.word_wrap = True
        para = box.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER
        title_pt = style.cover_title_pt if s.layout_type is LayoutType.TITLE else style.section_pt
        _blocks.add_rich_text(para, s.title, size=Pt(title_pt), bold=True, style=style, color=style.title_rgb)
        if style.accent_bar:  # centered accent rule under the big title
            rule_w = int(Inches(3.2))
            _accent_rect(slide, (int(slide_w) - rule_w) // 2, int(Inches(4.05)), rule_w, int(Inches(0.05)), style.accent_rgb)
        if style.page_numbers and s.layout_type is LayoutType.SECTION and page_no:
            _add_page_number(slide, prs, style, page_no)
        content_top = int(Inches(4.4))
    else:
        box = slide.shapes.add_textbox(content_left, int(Inches(0.3)), content_width, int(Inches(1.0)))
        box.text_frame.word_wrap = True
        para = box.text_frame.paragraphs[0]
        _blocks.add_rich_text(para, s.title, size=Pt(style.title_pt), bold=True, style=style, color=style.title_rgb)
        if style.accent_bar:  # short accent rule under the title
            _accent_rect(slide, content_left, int(Inches(1.22)), int(Inches(1.8)), int(Inches(0.045)), style.accent_rgb)
        if style.page_numbers and page_no:
            _add_page_number(slide, prs, style, page_no)
        content_top = int(Inches(1.5))

    if not s.blocks:
        return

    content_h = int(slide_h) - content_top - int(_MARGIN)
    content = (content_left, content_top, content_width, content_h)
    gap = int(Inches(0.2))

    if s.layout_type is LayoutType.TOC:
        _render_toc(slide, s, content, style)
        return

    regions = _regions_for(s, content, gap)
    if regions is not None:
        for block, region in zip(s.blocks, regions):
            _render_block(slide, block, region, renderer, asset_resolver, style, icon_resolver)
        return

    # Vertical-stack fallback: weighted full-width slices.
    vgap = int(Inches(0.15))
    n = len(s.blocks)
    fracs = _balanced_fractions([b.type for b in s.blocks])
    usable_h = content_h - vgap * (n - 1)
    cursor = content_top
    for block, f in zip(s.blocks, fracs):
        slice_h = int(usable_h * f)
        region = (content_left, cursor, content_width, slice_h)
        _render_block(slide, block, region, renderer, asset_resolver, style, icon_resolver)
        cursor += slice_h + vgap


def compile_deck(
    deck: Deck,
    out_path: str | Path,
    *,
    template: Optional[str | Path] = None,
    formula_renderer: Optional[FormulaRenderer] = None,
    asset_resolver: Optional[dict] = None,
    style: StyleProfile | str | None = None,
    icon_resolver=None,
) -> Path:
    """Render a `Deck` to a native, editable `.pptx` and return the output path.

    When `template` is a `.pptx` path, it is used as the base presentation so the output inherits its
    theme, fonts, and slide size. ``style`` selects a `StyleProfile` (fonts/sizes/colors; default
    ``academic``). ``asset_resolver`` maps a figure block's ``asset_id`` to a rendered image path.
    """
    profile = style if isinstance(style, StyleProfile) else get_style(style)
    if template is None and profile.base_template and Path(profile.base_template).is_file():
        template = profile.base_template  # imported template: inherit its master/theme natively
    prs = Presentation(str(template)) if template else Presentation()
    if template is None and profile.widescreen:  # 16:9 unless a template dictates its own size
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
    renderer = formula_renderer or NullFormulaRenderer()
    layout = _blank_layout(prs)

    for i, slide_ir in enumerate(deck.slides, start=1):
        slide = prs.slides.add_slide(layout)
        _render_slide(prs, slide, slide_ir, renderer, asset_resolver, profile, page_no=i, icon_resolver=icon_resolver)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out
