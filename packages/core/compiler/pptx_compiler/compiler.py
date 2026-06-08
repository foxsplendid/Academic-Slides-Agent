"""Deterministic Slide-IR -> native .pptx compiler.

Pure rendering (no AI): same Deck in -> same pptx structure out. Uses explicit positioning so
it is template-agnostic; placeholder/Manifest binding is a later change (add-template-mapper).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from slide_ir import (
    BulletBlock,
    ChartBlock,
    Deck,
    DiagramBlock,
    FigureBlock,
    FormulaBlock,
    LayoutType,
    SlideIR,
    TableBlock,
)

from . import blocks as _blocks
from .formula_renderer import FormulaRenderer, NullFormulaRenderer
from .style import ACADEMIC, StyleProfile, get_style

_DEFAULT_STYLE = ACADEMIC

_MARGIN = Inches(0.5)
_CENTERED = (LayoutType.TITLE, LayoutType.SECTION)
# Figures dominate; tables/formulas need room; bullets are compact. Used for weighted region heights.
_BLOCK_WEIGHT = {"figure": 3.2, "chart": 3.0, "diagram": 3.0, "table": 2.0, "formula": 1.6, "bullets": 1.0}
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


def _blank_layout(prs):
    """Pick a content-free layout so we control positioning ourselves."""
    layouts = list(prs.slide_layouts)
    for layout in layouts:
        if "blank" in (layout.name or "").lower():
            return layout
    return min(layouts, key=lambda layout: len(list(layout.placeholders)))


def _render_block(slide, block, region, renderer: FormulaRenderer, asset_resolver=None, style=_DEFAULT_STYLE):
    if isinstance(block, TableBlock):
        _blocks.render_table(slide, block, region, style)
    elif isinstance(block, BulletBlock):
        _blocks.render_bullets(slide, block, region, style)
    elif isinstance(block, FormulaBlock):
        _blocks.render_formula(slide, block, region, renderer)
    elif isinstance(block, FigureBlock):
        _blocks.render_figure(slide, block, region, asset_resolver, style)
    elif isinstance(block, ChartBlock):
        _blocks.render_chart(slide, block, region)
    elif isinstance(block, DiagramBlock):
        from .diagram import render_diagram

        render_diagram(slide, block, region, style)


def _render_slide(prs, slide, s: SlideIR, renderer: FormulaRenderer, asset_resolver=None, style=_DEFAULT_STYLE) -> None:
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
        content_top = int(Inches(4.4))
    else:
        box = slide.shapes.add_textbox(content_left, int(Inches(0.3)), content_width, int(Inches(1.0)))
        box.text_frame.word_wrap = True
        para = box.text_frame.paragraphs[0]
        _blocks.add_rich_text(para, s.title, size=Pt(style.title_pt), bold=True, style=style, color=style.title_rgb)
        content_top = int(Inches(1.5))

    if not s.blocks:
        return

    content_h = int(slide_h) - content_top - int(_MARGIN)
    gap = int(Inches(0.15))
    n = len(s.blocks)
    fracs = _balanced_fractions([b.type for b in s.blocks])
    usable_h = content_h - gap * (n - 1)
    cursor = content_top
    for block, f in zip(s.blocks, fracs):
        slice_h = int(usable_h * f)
        region = (content_left, cursor, content_width, slice_h)
        _render_block(slide, block, region, renderer, asset_resolver, style)
        cursor += slice_h + gap


def compile_deck(
    deck: Deck,
    out_path: str | Path,
    *,
    template: Optional[str | Path] = None,
    formula_renderer: Optional[FormulaRenderer] = None,
    asset_resolver: Optional[dict] = None,
    style: StyleProfile | str | None = None,
) -> Path:
    """Render a `Deck` to a native, editable `.pptx` and return the output path.

    When `template` is a `.pptx` path, it is used as the base presentation so the output inherits its
    theme, fonts, and slide size. ``style`` selects a `StyleProfile` (fonts/sizes/colors; default
    ``academic``). ``asset_resolver`` maps a figure block's ``asset_id`` to a rendered image path.
    """
    profile = style if isinstance(style, StyleProfile) else get_style(style)
    prs = Presentation(str(template)) if template else Presentation()
    if template is None and profile.widescreen:  # 16:9 unless a template dictates its own size
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
    renderer = formula_renderer or NullFormulaRenderer()
    layout = _blank_layout(prs)

    for slide_ir in deck.slides:
        slide = prs.slides.add_slide(layout)
        _render_slide(prs, slide, slide_ir, renderer, asset_resolver, profile)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out
