"""Style profiles — the design tokens (fonts/sizes/colors) the compiler applies.

A "template" for our deck is a profile of tokens, not a `.pptx` master (the reference 组会 look is
per-shape manual formatting, not a theme). `ACADEMIC` captures the established/user-derived tokens, so
the default render is unchanged; selecting another profile swaps the look.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx.dml.color import RGBColor


@dataclass(frozen=True)
class StyleProfile:
    name: str
    ea_font: str  # East-Asian typeface (CJK)
    latin_font: str  # Latin/number typeface
    title_pt: float  # content-slide title
    cover_title_pt: float  # title-slide title
    section_pt: float  # section-divider title
    body_pt: float  # bullets
    caption_pt: float  # figure caption
    table_header_pt: float
    table_body_pt: float
    emphasis_rgb: RGBColor  # the **…** highlight color
    node_fill_rgb: RGBColor  # diagram node fill
    node_line_rgb: RGBColor  # diagram node / connector line
    widescreen: bool = True


# The established tokens (derived from the user's academic 组会 deck) — default, so output is unchanged.
ACADEMIC = StyleProfile(
    name="academic",
    ea_font="黑体",
    latin_font="Times New Roman",
    title_pt=28.0,
    cover_title_pt=40.0,
    section_pt=32.0,
    body_pt=16.0,
    caption_pt=11.0,
    table_header_pt=14.0,
    table_body_pt=12.0,
    emphasis_rgb=RGBColor(0xFF, 0x00, 0x00),
    node_fill_rgb=RGBColor(0xDC, 0xE6, 0xF1),
    node_line_rgb=RGBColor(0x44, 0x72, 0xC4),
)

# A clearly-different profile to prove swapping (sans-serif + teal accent).
MODERN_TEAL = StyleProfile(
    name="modern_teal",
    ea_font="微软雅黑",
    latin_font="Calibri",
    title_pt=26.0,
    cover_title_pt=40.0,
    section_pt=30.0,
    body_pt=16.0,
    caption_pt=11.0,
    table_header_pt=14.0,
    table_body_pt=12.0,
    emphasis_rgb=RGBColor(0x00, 0x80, 0x80),
    node_fill_rgb=RGBColor(0xD5, 0xEF, 0xEC),
    node_line_rgb=RGBColor(0x00, 0x80, 0x80),
)

_PROFILES = {p.name: p for p in (ACADEMIC, MODERN_TEAL)}


def get_style(name: str | None) -> StyleProfile:
    """Resolve a profile by name; unknown/None -> ACADEMIC."""
    return _PROFILES.get((name or "").lower(), ACADEMIC)
