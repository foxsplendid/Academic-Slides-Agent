"""Render individual Slide-IR blocks into native python-pptx shapes within a region.

A region is an EMU tuple ``(left, top, width, height)``.
"""

from __future__ import annotations

from pathlib import Path

from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from slide_ir import BulletBlock, FigureBlock, FormulaBlock, TableBlock

from .formula_renderer import FormulaRenderer

Region = tuple[int, int, int, int]


def render_bullets(slide, block: BulletBlock, region: Region):
    left, top, width, height = region
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(block.items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {item}"
        p.font.size = Pt(18)
    return box


def render_table(slide, block: TableBlock, region: Region):
    left, top, width, height = region
    n_cols = len(block.columns)
    n_rows = len(block.rows) + 1  # header + data
    graphic_frame = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = graphic_frame.table

    for c, name in enumerate(block.columns):
        cell = table.cell(0, c)
        cell.text = str(name)
        for para in cell.text_frame.paragraphs:
            para.font.bold = True
            para.font.size = Pt(14)

    for r, row in enumerate(block.rows, start=1):
        for c in range(n_cols):
            cell = table.cell(r, c)
            cell.text = str(row[c]) if c < len(row) else ""
            for para in cell.text_frame.paragraphs:
                para.font.size = Pt(12)

    return graphic_frame


def render_formula(slide, block: FormulaBlock, region: Region, renderer: FormulaRenderer):
    left, top, width, height = region
    image = None
    try:
        image = renderer.to_image(block.latex)
    except Exception:
        image = None
    if image is not None and Path(image).exists():
        return slide.shapes.add_picture(str(image), left, top, width=width)

    # Text fallback: place the LaTeX as editable, centered text.
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = block.latex
    p.font.size = Pt(20)
    p.alignment = PP_ALIGN.CENTER
    return box


def render_figure(slide, block: FigureBlock, region: Region):
    left, top, width, height = region
    candidate = Path(block.asset_id)
    if candidate.is_file():
        return slide.shapes.add_picture(str(candidate), left, top, width=width)

    # Placeholder when the asset is not resolvable yet (Evidence Pool is a later change).
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    text = f"[figure: {block.asset_id}]"
    if block.caption:
        text += f"\n{block.caption}"
    tf.paragraphs[0].text = text
    return box
