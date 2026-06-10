"""Style profiles — the design tokens (fonts/sizes/colors/theme chrome) the compiler applies.

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
    title_rgb: RGBColor | None = None  # slide-title color (None = theme default / black)
    # --- theme chrome (deck-level decor; all deterministic shapes) ---
    accent_rgb: RGBColor = RGBColor(0x8B, 0x1A, 0x1A)  # accent bar / divider band / header fills
    accent_bar: bool = True  # thin accent rule under content-slide titles
    page_numbers: bool = True  # small page number bottom-right (content slides)
    muted_rgb: RGBColor = RGBColor(0x80, 0x80, 0x80)  # page numbers / secondary text
    # Text INSIDE autoshapes must be explicit: PowerPoint's shape style defaults it to white,
    # which vanishes on our light card fills. Tokens follow the academic palette (#333 body).
    text_rgb: RGBColor = RGBColor(0x33, 0x33, 0x33)  # body text on cards/nodes
    card_fill_rgb: RGBColor = RGBColor(0xF5, 0xF7, 0xFA)  # callout/stat card background
    card_line_rgb: RGBColor = RGBColor(0xD0, 0xD7, 0xE0)  # card border
    # --- data graphics ---
    chart_palette: tuple[RGBColor, ...] = (
        RGBColor(0x2F, 0x5E, 0x8E),  # deep blue
        RGBColor(0xC0, 0x3A, 0x2B),  # brick red
        RGBColor(0x6B, 0x8E, 0x4E),  # olive green
        RGBColor(0xC8, 0x8A, 0x2D),  # ochre
        RGBColor(0x5B, 0x4E, 0x77),  # plum
        RGBColor(0x4E, 0x8E, 0x8B),  # teal-gray
    )
    chart_axis_pt: float = 11.0  # axis tick labels / legend
    table_header_rgb: RGBColor = RGBColor(0x2F, 0x5E, 0x8E)  # header row fill
    table_band_rgb: RGBColor = RGBColor(0xEF, 0xF3, 0xF8)  # zebra banding fill


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
    accent_rgb=RGBColor(0x8B, 0x1A, 0x1A),  # deep academic red, matches the red emphasis
    table_header_rgb=RGBColor(0x3A, 0x3A, 0x3A),  # near-black header suits the 黑体/red look
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
    title_rgb=RGBColor(0x00, 0x80, 0x80),  # teal titles (exercises the title-color token)
    accent_rgb=RGBColor(0x00, 0x80, 0x80),
    table_header_rgb=RGBColor(0x00, 0x80, 0x80),
)

_PROFILES = {p.name: p for p in (ACADEMIC, MODERN_TEAL)}


def get_style(name: str | None) -> StyleProfile:
    """Resolve a profile by name; unknown/None -> ACADEMIC."""
    return _PROFILES.get((name or "").lower(), ACADEMIC)
