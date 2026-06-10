"""VisualCanvas (premium tier): constrained full-page SVG -> editable DrawingML slides.

The LLM authors a whole 1280x720 page as SVG (free composition: cards, annotated charts, bespoke
diagrams). Safety comes from three layers, none of which trusts the model:
1. `validate_canvas_svg` — closed bans (scripts, foreignObject, animation, external refs, images),
   required viewBox, size cap. Findings are repair-routable.
2. The vendored MIT finalize passes repair LLM SVG quirks (entities, tspans, overlapping text runs,
   rounded rects) deterministically.
3. The vendored MIT svg2pptx converter emits native text boxes + custGeom vectors — editable, never
   a screenshot. All vendored code is arms-length (see packages/vendor/svg2pptx/README.md).
"""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

CANVAS_VIEWBOX = "0 0 1280 720"
_MAX_SVG_CHARS = 300_000
_BANNED_TAGS = {"script", "foreignObject", "animate", "animateTransform", "animateMotion", "set", "iframe", "audio", "video", "image"}


def validate_canvas_svg(svg: str) -> list[str]:
    """Return findings (empty == valid). The closed-ban list keeps the canvas safe and convertible."""
    findings: list[str] = []
    if len(svg) > _MAX_SVG_CHARS:
        return [f"canvas svg too large ({len(svg)} > {_MAX_SVG_CHARS} chars)"]
    try:
        root = etree.fromstring(svg.encode("utf-8"))
    except Exception as err:
        return [f"canvas svg is not well-formed XML: {str(err)[:160]}"]
    tag = etree.QName(root).localname if root.tag else ""
    if tag != "svg":
        return ["canvas root element must be <svg>"]
    viewbox = (root.get("viewBox") or "").strip()
    if re.sub(r"\s+", " ", viewbox) != CANVAS_VIEWBOX:
        findings.append(f"canvas viewBox must be '{CANVAS_VIEWBOX}' (got '{viewbox or 'none'}')")
    for el in root.iter():
        name = etree.QName(el).localname if isinstance(el.tag, str) else ""
        if name in _BANNED_TAGS:
            findings.append(f"canvas contains banned element <{name}>")
        for attr, val in el.attrib.items():
            local = attr.rsplit("}", 1)[-1]
            if local == "href" and not str(val).startswith("#"):
                findings.append(f"canvas href must be internal ('#…'), got '{str(val)[:60]}'")
            if local.startswith("on"):  # onload/onclick handlers
                findings.append(f"canvas contains script handler attribute '{local}'")
        style_val = el.get("style") or ""
        if "url(" in style_val and "url(#" not in style_val:
            findings.append("canvas style references an external url()")
    return findings


def _repair_canvas_file(svg_path: Path) -> None:
    """Run the deterministic finalize passes that make LLM SVG PowerPoint-safe (best effort)."""
    try:
        from asa_svg2pptx.svg_finalize.repair_svg import repair_svg_file

        repair_svg_file(svg_path)
    except Exception:
        pass
    for mod_name, fn_name in (
        ("flatten_tspan", "flatten_text_in_svg"),
        ("merge_adjacent_text", "merge_adjacent_text_in_svg"),
        ("svg_text_reflow", "reflow_text_in_svg"),
        ("svg_rect_to_path", "convert_rounded_rects_in_svg"),
    ):
        try:
            mod = __import__(f"asa_svg2pptx.svg_finalize.{mod_name}", fromlist=[fn_name])
            getattr(mod, fn_name)(svg_path)
        except Exception:
            continue


def canvas_engine_available() -> bool:
    try:
        import asa_svg2pptx  # noqa: F401

        return True
    except Exception:
        return False


def inject_canvas_slides(pptx_path: str | Path, canvases: dict[int, str]) -> None:
    """Replace slide N (1-based) of a saved deck with the converted canvas SVG content.

    v1 canvases are vector+text only (images banned by the guard), so the existing slide rels are
    kept untouched and only the slide XML is swapped — the safest possible package surgery."""
    if not canvases:
        return
    from asa_svg2pptx.svg_to_pptx.builder import convert_svg_to_slide_shapes, prepare_svg_file_for_render

    pptx_path = Path(pptx_path)
    work = Path(tempfile.mkdtemp(prefix="asa_canvas_"))
    try:
        extract = work / "pkg"
        with zipfile.ZipFile(pptx_path, "r") as zf:
            zf.extractall(extract)
        for slide_num, svg in canvases.items():
            svg_file = work / f"canvas_{slide_num}.svg"
            svg_file.write_text(svg, encoding="utf-8")
            _repair_canvas_file(svg_file)
            prepared = prepare_svg_file_for_render(svg_file)
            try:
                slide_xml, media, rels = convert_svg_to_slide_shapes(prepared, slide_num)
            finally:
                Path(prepared).unlink(missing_ok=True)
            if media or rels:  # guard bans images, so this indicates an engine surprise — fail open
                continue
            target = extract / "ppt" / "slides" / f"slide{slide_num}.xml"
            if target.is_file():
                target.write_text(slide_xml, encoding="utf-8")
        out_tmp = work / "out.pptx"
        with zipfile.ZipFile(out_tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(extract.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(extract).as_posix())
        shutil.copyfile(out_tmp, pptx_path)
    finally:
        shutil.rmtree(work, ignore_errors=True)


_CANVAS_W, _CANVAS_H = 1280.0, 720.0


def _est_text_width(text: str, size: float) -> float:
    """CJK ~= 1.0 em, Latin/digit ~= 0.55 em — same estimator family the bullet fitter uses."""
    return sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in text) * size


def lint_canvas_svg(svg: str) -> list[str]:
    """Deterministic geometry lint for canvas pages: estimated text overflow past the canvas edge
    and text-on-text collisions. Conservative on purpose (transforms are skipped) — its findings
    feed the authoring retry loop, so false positives would burn LLM attempts."""
    try:
        root = etree.fromstring(svg.encode("utf-8"))
    except Exception:
        return []  # well-formedness is the guard's job
    texts: list[tuple[float, float, float, float, str]] = []  # (x0, x1, y, size, snippet)

    def walk(el, skip: bool) -> None:
        name = etree.QName(el).localname if isinstance(el.tag, str) else ""
        skip = skip or name == "defs" or el.get("transform") is not None
        if name == "text" and not skip:
            content = "".join(el.itertext()).strip()
            if content:
                try:
                    x = float(el.get("x", "0"))
                    y = float(el.get("y", "0"))
                    size = float((el.get("font-size") or "16").replace("px", ""))
                except ValueError:
                    return
                w = _est_text_width(content, size)
                anchor = el.get("text-anchor") or ""
                x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
                texts.append((x0, x0 + w, y, size, content[:24]))
        for child in el:
            walk(child, skip)

    walk(root, False)
    findings: list[str] = []
    for x0, x1, y, size, snip in texts:
        if x1 > _CANVAS_W + 12 or x0 < -12:
            findings.append(f"文本可能超出画布右/左边界: “{snip}…” (x≈{x0:.0f}-{x1:.0f})")
        if y > _CANVAS_H - 4 or y - size < 0:
            findings.append(f"文本可能超出画布上下边界: “{snip}…” (y≈{y:.0f})")
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a, b = texts[i], texts[j]
            if abs(a[2] - b[2]) < 0.6 * min(a[3], b[3]):
                inter = min(a[1], b[1]) - max(a[0], b[0])
                if inter > 0.25 * min(a[1] - a[0], b[1] - b[0]) and inter > 8:
                    findings.append(f"两段文本疑似重叠: “{a[4]}…” 与 “{b[4]}…” (y≈{a[2]:.0f})")
    return findings[:6]
