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

_MARGIN = Inches(0.5)
_CENTERED = (LayoutType.TITLE, LayoutType.SECTION)
# Figures dominate; tables/formulas need room; bullets are compact. Used for weighted region heights.
_BLOCK_WEIGHT = {"figure": 3.2, "chart": 3.0, "diagram": 3.0, "table": 2.0, "formula": 1.6, "bullets": 1.0}


def _blank_layout(prs):
    """Pick a content-free layout so we control positioning ourselves."""
    layouts = list(prs.slide_layouts)
    for layout in layouts:
        if "blank" in (layout.name or "").lower():
            return layout
    return min(layouts, key=lambda layout: len(list(layout.placeholders)))


def _render_block(slide, block, region, renderer: FormulaRenderer, asset_resolver=None):
    if isinstance(block, TableBlock):
        _blocks.render_table(slide, block, region)
    elif isinstance(block, BulletBlock):
        _blocks.render_bullets(slide, block, region)
    elif isinstance(block, FormulaBlock):
        _blocks.render_formula(slide, block, region, renderer)
    elif isinstance(block, FigureBlock):
        _blocks.render_figure(slide, block, region, asset_resolver)
    elif isinstance(block, ChartBlock):
        _blocks.render_chart(slide, block, region)
    elif isinstance(block, DiagramBlock):
        from .diagram import render_diagram

        render_diagram(slide, block, region)


def _render_slide(prs, slide, s: SlideIR, renderer: FormulaRenderer, asset_resolver=None) -> None:
    slide_w, slide_h = prs.slide_width, prs.slide_height
    content_left = int(_MARGIN)
    content_width = int(slide_w) - 2 * int(_MARGIN)

    if s.layout_type in _CENTERED:
        box = slide.shapes.add_textbox(content_left, int(Inches(2.2)), content_width, int(Inches(2.0)))
        box.text_frame.word_wrap = True
        para = box.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER
        _blocks.add_rich_text(
            para, s.title, size=Pt(40 if s.layout_type is LayoutType.TITLE else 32), bold=True
        )
        content_top = int(Inches(4.4))
    else:
        box = slide.shapes.add_textbox(content_left, int(Inches(0.3)), content_width, int(Inches(1.0)))
        box.text_frame.word_wrap = True
        para = box.text_frame.paragraphs[0]
        _blocks.add_rich_text(para, s.title, size=Pt(28), bold=True)
        content_top = int(Inches(1.5))

    if not s.blocks:
        return

    content_h = int(slide_h) - content_top - int(_MARGIN)
    gap = int(Inches(0.15))
    n = len(s.blocks)
    weights = [_BLOCK_WEIGHT.get(b.type, 1.0) for b in s.blocks]
    total_w = sum(weights)
    usable_h = content_h - gap * (n - 1)
    cursor = content_top
    for block, w in zip(s.blocks, weights):
        slice_h = int(usable_h * w / total_w)
        region = (content_left, cursor, content_width, slice_h)
        _render_block(slide, block, region, renderer, asset_resolver)
        cursor += slice_h + gap


def compile_deck(
    deck: Deck,
    out_path: str | Path,
    *,
    template: Optional[str | Path] = None,
    formula_renderer: Optional[FormulaRenderer] = None,
    asset_resolver: Optional[dict] = None,
) -> Path:
    """Render a `Deck` to a native, editable `.pptx` and return the output path.

    When `template` is a `.pptx` path, it is used as the base presentation so the output
    inherits its theme, fonts, and slide size. ``asset_resolver`` maps a figure block's
    ``asset_id`` to a rendered image path (from the Evidence Pool).
    """
    prs = Presentation(str(template)) if template else Presentation()
    if template is None:  # default to 16:9 widescreen to match the reference 组会 deck
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
    renderer = formula_renderer or NullFormulaRenderer()
    layout = _blank_layout(prs)

    for slide_ir in deck.slides:
        slide = prs.slides.add_slide(layout)
        _render_slide(prs, slide, slide_ir, renderer, asset_resolver)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out
