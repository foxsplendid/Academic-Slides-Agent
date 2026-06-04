"""Render individual Slide-IR blocks into native python-pptx shapes within a region.

A region is an EMU tuple ``(left, top, width, height)``. Text is rendered CJK-aware (East-Asian +
Latin typefaces) and supports a ``**…**`` emphasis convention rendered as bold red runs, matching the
reference 组会 deck style (docs/SPEC.md styling).
"""

from __future__ import annotations

import re
from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

from slide_ir import BulletBlock, FigureBlock, FormulaBlock, TableBlock

from .formula_renderer import FormulaRenderer

Region = tuple[int, int, int, int]

# Reference-deck styling: 黑体 for CJK, Times New Roman for Latin/numbers, red for emphasis.
EA_FONT = "黑体"
LATIN_FONT = "Times New Roman"
_RED = RGBColor(0xFF, 0x00, 0x00)
_EMPHASIS = re.compile(r"\*\*(.+?)\*\*")


def _set_ea(font, typeface: str) -> None:
    """Set the East-Asian typeface (`<a:ea>`); python-pptx's ``font.name`` only sets `<a:latin>`."""
    rpr = font._rPr
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = rpr.makeelement(qn("a:ea"), {})
        rpr.append(ea)
    ea.set("typeface", typeface)


def add_rich_text(paragraph, text: str, *, size, bold: bool = False) -> None:
    """Add runs to ``paragraph``, rendering ``**…**`` spans as bold red while the rest is default."""
    segments: list[tuple[str, bool]] = []
    pos = 0
    for m in _EMPHASIS.finditer(text):
        if m.start() > pos:
            segments.append((text[pos:m.start()], False))
        segments.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        segments.append((text[pos:], False))
    if not segments:
        segments = [(text, False)]
    for content, emph in segments:
        run = paragraph.add_run()
        run.text = content
        f = run.font
        f.size = size
        f.bold = bold or emph
        f.name = LATIN_FONT
        if emph:
            f.color.rgb = _RED
        _set_ea(f, EA_FONT)


def render_bullets(slide, block: BulletBlock, region: Region):
    left, top, width, height = region
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(block.items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        add_rich_text(p, f"• {item}", size=Pt(16))
    return box


def render_table(slide, block: TableBlock, region: Region):
    left, top, width, height = region
    n_cols = len(block.columns)
    n_rows = len(block.rows) + 1  # header + data
    graphic_frame = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = graphic_frame.table

    for c, name in enumerate(block.columns):
        cell = table.cell(0, c)
        cell.text = ""
        add_rich_text(cell.text_frame.paragraphs[0], str(name), size=Pt(14), bold=True)

    for r, row in enumerate(block.rows, start=1):
        for c in range(n_cols):
            cell = table.cell(r, c)
            cell.text = ""
            value = str(row[c]) if c < len(row) else ""
            add_rich_text(cell.text_frame.paragraphs[0], value, size=Pt(12))

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


def render_figure(slide, block: FigureBlock, region: Region, asset_resolver=None):
    left, top, width, height = region
    # Resolve the asset_id to a rendered image path (Evidence Pool), then fall back to a raw path.
    resolved = asset_resolver.get(block.asset_id) if asset_resolver else None
    candidate = Path(resolved) if resolved else Path(block.asset_id)
    if candidate.is_file():
        caption_h = int(Pt(28)) if block.caption else 0  # reserve a line for the caption
        avail_h = max(1, height - caption_h)
        # Fit the image into (width, avail_h) preserving aspect ratio; center horizontally.
        try:
            from PIL import Image

            with Image.open(str(candidate)) as im:
                iw, ih = im.size
            scale = min(width / iw, avail_h / ih)
            w, h = max(1, int(iw * scale)), max(1, int(ih * scale))
        except Exception:
            w, h = width, avail_h  # defensive (python-pptx already requires Pillow)
        x = left + (width - w) // 2
        pic = slide.shapes.add_picture(str(candidate), x, top, width=w, height=h)
        if block.caption:
            cap = slide.shapes.add_textbox(left, top + h, width, caption_h)
            cap.text_frame.word_wrap = True
            para = cap.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.CENTER
            add_rich_text(para, block.caption, size=Pt(11))
        return pic

    # Placeholder when the asset is not resolvable (e.g. the planner described a figure with no asset).
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    text = f"[figure: {block.asset_id}]"
    if block.caption:
        text += f"\n{block.caption}"
    add_rich_text(tf.paragraphs[0], text, size=Pt(14))
    return box
