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
