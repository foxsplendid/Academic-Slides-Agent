"""Render individual Slide-IR blocks into native python-pptx shapes within a region.

A region is an EMU tuple ``(left, top, width, height)``. Text is rendered CJK-aware (East-Asian +
Latin typefaces) and supports a ``**…**`` emphasis convention rendered as bold red runs, matching the
reference 组会 deck style (docs/SPEC.md styling).
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

from slide_ir import BulletBlock, ChartBlock, FigureBlock, FormulaBlock, TableBlock

from .formula_renderer import FormulaRenderer
from .style import ACADEMIC, StyleProfile

Region = tuple[int, int, int, int]

EA_FONT = ACADEMIC.ea_font  # kept for back-compat; per-render styling comes from the StyleProfile
LATIN_FONT = ACADEMIC.latin_font
_EMPHASIS = re.compile(r"\*\*(.+?)\*\*")


def _set_ea(font, typeface: str) -> None:
    """Set the East-Asian typeface (`<a:ea>`); python-pptx's ``font.name`` only sets `<a:latin>`."""
    rpr = font._rPr
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = rpr.makeelement(qn("a:ea"), {})
        rpr.append(ea)
    ea.set("typeface", typeface)


def add_rich_text(paragraph, text: str, *, size, bold: bool = False, style: StyleProfile = ACADEMIC, color=None) -> None:
    """Add runs to ``paragraph``, rendering ``**…**`` spans as bold emphasis-colored while the rest uses
    ``color`` (or the theme default when None)."""
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
        f.name = style.latin_font
        if emph:
            f.color.rgb = style.emphasis_rgb
        elif color is not None:
            f.color.rgb = color
        _set_ea(f, style.ea_font)


_EMU_PER_PT = 12700.0


def _display_width(text: str) -> float:
    """CJK chars occupy ~1 em, Latin ~0.5 em — used to estimate wrapped line count."""
    return sum(1.0 if ord(c) > 0x2E80 else 0.5 for c in text)


def _fit_font(items: list[str], width: int, height: int, *, base: float = 16.0, floor: float = 10.0) -> float:
    """Measure, then place: shrink the font until the bullets' estimated height fits the region."""
    w_pt = max(width / _EMU_PER_PT, 1.0)
    h_pt = max(height / _EMU_PER_PT, 1.0)
    f = base
    while f > floor:
        per_line = max(w_pt / f, 1.0)  # ~em units that fit on one line at size f
        lines = sum(max(1, math.ceil(_display_width("• " + it) / per_line)) for it in items)
        if lines * f * 1.28 <= h_pt:  # 1.28 ≈ line spacing
            break
        f -= 1.0
    return max(f, floor)


def render_bullets(slide, block: BulletBlock, region: Region, style: StyleProfile = ACADEMIC):
    left, top, width, height = region
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    size = Pt(_fit_font(block.items, width, height, base=style.body_pt))  # auto-shrink dense text
    for i, item in enumerate(block.items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        add_rich_text(p, f"• {item}", size=size, style=style)
    return box


def render_table(slide, block: TableBlock, region: Region, style: StyleProfile = ACADEMIC):
    left, top, width, height = region
    n_cols = len(block.columns)
    n_rows = len(block.rows) + 1  # header + data
    graphic_frame = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = graphic_frame.table

    for c, name in enumerate(block.columns):
        cell = table.cell(0, c)
        cell.text = ""
        add_rich_text(cell.text_frame.paragraphs[0], str(name), size=Pt(style.table_header_pt), bold=True, style=style)

    for r, row in enumerate(block.rows, start=1):
        for c in range(n_cols):
            cell = table.cell(r, c)
            cell.text = ""
            value = str(row[c]) if c < len(row) else ""
            add_rich_text(cell.text_frame.paragraphs[0], value, size=Pt(style.table_body_pt), style=style)

    return graphic_frame


_CATEGORY_CHARTS = {
    "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
}


def render_chart(slide, block: ChartBlock, region: Region):
    """Render a native, editable PowerPoint chart (not an image)."""
    left, top, width, height = region
    if block.chart_type == "scatter":
        data = XyChartData()
        for s in block.series:
            series = data.add_series(s.name or "series")
            xs = s.x or list(range(1, len(s.values) + 1))
            for x, y in zip(xs, s.values):
                series.add_data_point(float(x), float(y))
        frame = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, left, top, width, height, data)
    else:
        n = len(block.categories) if block.categories else max(len(s.values) for s in block.series)
        cats = block.categories or [str(i + 1) for i in range(n)]
        data = CategoryChartData()
        data.categories = cats
        for s in block.series:
            vals = (list(s.values)[:n] + [0.0] * n)[:n]  # pad/truncate to the category count
            data.add_series(s.name or "series", vals)
        ctype = _CATEGORY_CHARTS.get(block.chart_type, XL_CHART_TYPE.COLUMN_CLUSTERED)
        frame = slide.shapes.add_chart(ctype, left, top, width, height, data)
    chart = frame.chart
    if block.title:
        chart.has_title = True
        chart.chart_title.text_frame.text = block.title
    chart.has_legend = len(block.series) > 1 or block.chart_type == "pie"
    return frame


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


def render_figure(slide, block: FigureBlock, region: Region, asset_resolver=None, style: StyleProfile = ACADEMIC):
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
            add_rich_text(para, block.caption, size=Pt(style.caption_pt), style=style)
        return pic

    # Placeholder when the asset is not resolvable (e.g. the planner described a figure with no asset).
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    text = f"[figure: {block.asset_id}]"
    if block.caption:
        text += f"\n{block.caption}"
    add_rich_text(tf.paragraphs[0], text, size=Pt(14), style=style)
    return box
