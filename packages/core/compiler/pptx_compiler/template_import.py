"""Import a user .pptx as a style: extract theme tokens (fonts, accent palette) into a
StyleProfile whose ``base_template`` points at the file, so compiling inherits the real master
(background, layouts, theme) natively while our renderers use matching tokens.

Pure-deterministic extraction (zip + XML; no AI, no new deps — lxml ships with python-pptx).
"""

from __future__ import annotations

import dataclasses
import re
import zipfile
from pathlib import Path

from lxml import etree
from pptx.dml.color import RGBColor

from .style import ACADEMIC, StyleProfile, register_style

_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS = {"a": _A}


def _rgb(hexstr: str) -> RGBColor:
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))


def extract_style_from_pptx(pptx_path: str | Path, name: str) -> StyleProfile:
    """Read theme1.xml and derive a StyleProfile (ACADEMIC sizes; template fonts + accent palette)."""
    pptx_path = Path(pptx_path)
    ea_font, latin_font = ACADEMIC.ea_font, ACADEMIC.latin_font
    accent = ACADEMIC.accent_rgb
    palette: tuple[RGBColor, ...] = ACADEMIC.chart_palette
    try:
        with zipfile.ZipFile(str(pptx_path)) as z:
            theme_name = next((n for n in z.namelist() if re.fullmatch(r"ppt/theme/theme\d+\.xml", n)), None)
            if theme_name:
                root = etree.fromstring(z.read(theme_name))
                major = root.find(".//a:fontScheme/a:majorFont", _NS)
                if major is not None:
                    latin = major.find("a:latin", _NS)
                    ea = major.find("a:ea", _NS)
                    if latin is not None and latin.get("typeface"):
                        latin_font = latin.get("typeface")
                    if ea is not None and ea.get("typeface"):
                        ea_font = ea.get("typeface")
                accents = []
                for i in range(1, 7):
                    el = root.find(f".//a:clrScheme/a:accent{i}/a:srgbClr", _NS)
                    if el is not None and el.get("val"):
                        accents.append(_rgb(el.get("val")))
                if accents:
                    accent = accents[0]
                    palette = tuple(accents) if len(accents) >= 3 else palette
    except Exception:
        pass  # fall back to ACADEMIC tokens; the master still carries the visual identity
    return dataclasses.replace(
        ACADEMIC,
        name=name.lower(),
        ea_font=ea_font,
        latin_font=latin_font,
        accent_rgb=accent,
        table_header_rgb=accent,
        chart_palette=palette,
        title_rgb=None,
        base_template=str(pptx_path),
    )


def profile_to_dict(p: StyleProfile) -> dict:
    return {
        "name": p.name,
        "ea_font": p.ea_font,
        "latin_font": p.latin_font,
        "accent": str(p.accent_rgb),
        "palette": [str(c) for c in p.chart_palette],
        "base_template": p.base_template,
    }


def profile_from_dict(d: dict) -> StyleProfile:
    return dataclasses.replace(
        ACADEMIC,
        name=str(d.get("name", "custom")).lower(),
        ea_font=d.get("ea_font") or ACADEMIC.ea_font,
        latin_font=d.get("latin_font") or ACADEMIC.latin_font,
        accent_rgb=_rgb(d["accent"]) if d.get("accent") else ACADEMIC.accent_rgb,
        table_header_rgb=_rgb(d["accent"]) if d.get("accent") else ACADEMIC.table_header_rgb,
        chart_palette=tuple(_rgb(c) for c in d.get("palette") or []) or ACADEMIC.chart_palette,
        title_rgb=None,
        base_template=d.get("base_template"),
    )


def import_template(pptx_path: str | Path, name: str) -> StyleProfile:
    """Extract + register; returns the registered profile."""
    profile = extract_style_from_pptx(pptx_path, name)
    register_style(profile)
    return profile
