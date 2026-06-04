"""Unit tests for the pptx compiler.

Each test maps to a scenario in
openspec/changes/add-pptx-compiler/specs/pptx-compiler/spec.md.
"""

from __future__ import annotations

import base64

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from slide_ir import (
    BulletBlock,
    Deck,
    FigureBlock,
    FormulaBlock,
    LayoutType,
    SlideIR,
    TableBlock,
)
from pptx_compiler import NullFormulaRenderer, compile_deck

# 1x1 PNG, used to exercise the image-embedding path without Pillow.
_PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _deck() -> Deck:
    return Deck(
        deck_id="d",
        slides=[
            SlideIR(slide_id="s1", layout_type=LayoutType.TITLE, title="Title"),
            SlideIR(
                slide_id="s2",
                layout_type=LayoutType.BULLET_EVIDENCE,
                title="Motivation",
                blocks=[BulletBlock(items=["alpha", "beta", "gamma"])],
            ),
            SlideIR(
                slide_id="s3",
                layout_type=LayoutType.TWO_COLUMN_TABLE,
                title="Results",
                blocks=[
                    TableBlock(
                        columns=["Sample", "87Sr/86Sr"],
                        rows=[["HT-1", "0.7041"], ["HT-2", "0.7039"]],
                    )
                ],
            ),
            SlideIR(
                slide_id="s4",
                layout_type=LayoutType.FORMULA_BANNER,
                title="Eps",
                blocks=[FormulaBlock(latex="E=mc^2")],
            ),
        ],
    )


def test_one_slide_per_ir_and_valid_pptx(tmp_path):
    out = compile_deck(_deck(), tmp_path / "out.pptx")
    assert out.exists()
    prs = Presentation(str(out))  # reopen -> valid PPTX
    assert len(prs.slides) == 4


def test_table_is_native(tmp_path):
    out = compile_deck(_deck(), tmp_path / "out.pptx")
    slide = Presentation(str(out)).slides[2]
    tables = [sh for sh in slide.shapes if sh.has_table]
    assert len(tables) == 1
    table = tables[0].table
    assert len(table.columns) == 2
    assert len(table.rows) == 3  # header + 2 data rows
    assert table.cell(0, 0).text == "Sample"


def test_bullets_text_present(tmp_path):
    out = compile_deck(_deck(), tmp_path / "out.pptx")
    slide = Presentation(str(out)).slides[1]
    texts = " ".join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
    for item in ("alpha", "beta", "gamma"):
        assert item in texts


def test_formula_text_fallback(tmp_path):
    out = compile_deck(_deck(), tmp_path / "out.pptx", formula_renderer=NullFormulaRenderer())
    slide = Presentation(str(out)).slides[3]
    texts = " ".join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
    assert "E=mc^2" in texts
    assert not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slide.shapes)


def test_formula_image_when_renderer_provides(tmp_path):
    img = tmp_path / "f.png"
    img.write_bytes(_PNG_1x1)

    class _ImgRenderer:
        def to_image(self, latex):
            return img

    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s",
                layout_type=LayoutType.FORMULA_BANNER,
                title="f",
                blocks=[FormulaBlock(latex="x^2")],
            )
        ],
    )
    out = compile_deck(deck, tmp_path / "o.pptx", formula_renderer=_ImgRenderer())
    slide = Presentation(str(out)).slides[0]
    assert any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slide.shapes)


def test_template_slide_size_inherited(tmp_path):
    template = tmp_path / "tmpl.pptx"
    base = Presentation()
    base.slide_width = Inches(13.333)
    base.slide_height = Inches(7.5)
    base.save(str(template))
    expected_w = Presentation(str(template)).slide_width

    out = compile_deck(_deck(), tmp_path / "out.pptx", template=template)
    result = Presentation(str(out))
    assert result.slide_width == expected_w


def test_deterministic_structure(tmp_path):
    deck = _deck()
    a = Presentation(str(compile_deck(deck, tmp_path / "a.pptx")))
    b = Presentation(str(compile_deck(deck, tmp_path / "b.pptx")))
    assert len(a.slides) == len(b.slides)

    def sig(prs):
        return [tuple(sh.shape_type for sh in slide.shapes) for slide in prs.slides]

    assert sig(a) == sig(b)


# --- improve-output-quality: styling -----------------------------------------


def test_fresh_deck_is_16_9(tmp_path):
    deck = Deck(deck_id="d", slides=[SlideIR(slide_id="s1", layout_type=LayoutType.TITLE, title="T")])
    prs = Presentation(str(compile_deck(deck, tmp_path / "w.pptx")))
    assert round(prs.slide_width / prs.slide_height, 3) == 1.778  # 16:9


def test_emphasis_span_becomes_red_bold_run(tmp_path):
    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s1",
                layout_type=LayoutType.BULLET_EVIDENCE,
                title="x",
                blocks=[BulletBlock(items=["plain **key** tail"])],
            )
        ],
    )
    prs = Presentation(str(compile_deck(deck, tmp_path / "e.pptx")))
    reds = [
        r
        for slide in prs.slides
        for sh in slide.shapes
        if sh.has_text_frame
        for p in sh.text_frame.paragraphs
        for r in p.runs
        if r.font.bold
        and r.font.color is not None
        and r.font.color.type is not None
        and str(r.font.color.rgb) == "FF0000"
    ]
    assert any(r.text == "key" for r in reds)


# --- add-figure-extraction: asset resolution ---------------------------------


def test_figure_resolved_via_resolver(tmp_path):
    img = tmp_path / "r.png"
    img.write_bytes(_PNG_1x1)
    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s",
                layout_type=LayoutType.FIGURE_CAPTION,
                title="f",
                blocks=[FigureBlock(asset_id="img1", caption="c")],
            )
        ],
    )
    out = compile_deck(deck, tmp_path / "fig.pptx", asset_resolver={"img1": str(img)})
    slide = Presentation(str(out)).slides[0]
    assert any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slide.shapes)


def _png(path, w, h):
    from PIL import Image

    Image.new("RGB", (w, h), (200, 200, 200)).save(str(path))
    return path


def test_figure_is_contained_and_centered(tmp_path):
    img = _png(tmp_path / "wide.png", 800, 200)  # wide image
    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s",
                layout_type=LayoutType.FIGURE_CAPTION,
                title="f",
                blocks=[FigureBlock(asset_id="i", caption="cap")],
            )
        ],
    )
    out = compile_deck(deck, tmp_path / "fit.pptx", asset_resolver={"i": str(img)})
    prs = Presentation(str(out))
    slide = prs.slides[0]
    pics = [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert pics
    pic = pics[0]
    content_w = prs.slide_width - 2 * Inches(0.5)
    assert pic.width <= content_w  # not forced past content width
    assert abs(pic.height / pic.width - 200 / 800) < 0.02  # aspect preserved
    # centered horizontally within the content area
    center = pic.left + pic.width / 2
    assert abs(center - prs.slide_width / 2) < Inches(0.2)


def test_figure_gets_more_room_than_bullets(tmp_path):
    img = _png(tmp_path / "sq.png", 400, 400)
    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s",
                layout_type=LayoutType.FIGURE_CAPTION,
                title="f",
                blocks=[FigureBlock(asset_id="i"), BulletBlock(items=["a", "b"])],
            )
        ],
    )
    out = compile_deck(deck, tmp_path / "room.pptx", asset_resolver={"i": str(img)})
    prs = Presentation(str(out))
    shapes = list(prs.slides[0].shapes)
    pic = next(sh for sh in shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE)
    bullets = next(sh for sh in shapes if sh.has_text_frame and "a" in sh.text_frame.text)
    # the figure region (square image fit) is taller than the bullets textbox
    assert pic.height > bullets.height


def test_unresolved_figure_falls_back_to_placeholder(tmp_path):
    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s",
                layout_type=LayoutType.FIGURE_CAPTION,
                title="f",
                blocks=[FigureBlock(asset_id="missing", caption="c")],
            )
        ],
    )
    out = compile_deck(deck, tmp_path / "ph.pptx", asset_resolver={})
    slide = Presentation(str(out)).slides[0]
    assert not any(sh.shape_type == MSO_SHAPE_TYPE.PICTURE for sh in slide.shapes)
    texts = " ".join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)
    assert "missing" in texts
