"""Composite (multi-panel) figure splitting — band-based recursive X-Y-cut, Pillow-only, AI-free.

Scientific figures are often one image stitched from sub-panels (A/B/C/D). When enabled
(``ASA_SPLIT_FIGURES``), `split_composite` detects full-span near-white gutters and cuts the image
into panel images. Deterministic (fits the locked architecture), conservative (opt-in; gated against
over-segmentation), and numpy-free — the per-row/col projection is the mean of a 1-px Pillow resize.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

WHITE_THRESH = 247  # a row/col is a "gutter" if its mean intensity >= this (near white)
MIN_GUTTER_FRAC = 0.025  # a separator band must span >= this fraction of the axis
MIN_PANEL_FRAC = 0.12  # each panel must be >= this fraction of the parent in BOTH dims
MIN_W, MIN_H = 600, 400  # below this the image is too small to be a real multi-panel figure
MIN_AREA_FRAC = 0.6  # panels must reconstruct >= this fraction of the parent area (else mis-detect)
MAX_PANELS = 12
MAX_DEPTH = 3


def _flat(img: Image.Image) -> list[float]:
    # Pillow 12 renamed getdata() -> get_flattened_data() (getdata removed in 14);
    # fall back to getdata() on Pillow < 12 (the project floor is Pillow>=10).
    flatten = getattr(img, "get_flattened_data", img.getdata)
    return list(flatten())


def _line_means(gray: Image.Image, axis: str) -> list[float]:
    """Per-row (axis='row') or per-column (axis='col') mean intensity, via a 1-px BOX resize."""
    w, h = gray.size
    if axis == "row":
        return _flat(gray.resize((1, h), Image.Resampling.BOX))
    return _flat(gray.resize((w, 1), Image.Resampling.BOX))


def _interior_cuts(means: list[float], axis_len: int) -> list[int]:
    """Centers of maximal interior near-white runs wide enough to be a separator band."""
    n = len(means)
    min_band = MIN_GUTTER_FRAC * axis_len
    cuts: list[int] = []
    i = 0
    while i < n:
        if means[i] >= WHITE_THRESH:
            j = i
            while j < n and means[j] >= WHITE_THRESH:
                j += 1
            if i > 0 and j < n and (j - i) >= min_band:  # interior (not edge) + wide enough
                cuts.append((i + j) // 2)
            i = j
        else:
            i += 1
    return cuts


def _split_box(gray: Image.Image, box: tuple[int, int, int, int], depth: int, out: list) -> None:
    left, top, right, bottom = box
    sub = gray.crop(box)
    w, h = sub.size
    col_cuts = _interior_cuts(_line_means(sub, "col"), w)  # vertical separators -> cut along x
    row_cuts = _interior_cuts(_line_means(sub, "row"), h)  # horizontal separators -> cut along y
    if depth >= MAX_DEPTH or (not col_cuts and not row_cuts):
        out.append(box)
        return
    if col_cuts:
        xs = [left] + [left + c for c in col_cuts] + [right]
        for i in range(len(xs) - 1):
            _split_box(gray, (xs[i], top, xs[i + 1], bottom), depth + 1, out)
    else:
        ys = [top] + [top + c for c in row_cuts] + [bottom]
        for i in range(len(ys) - 1):
            _split_box(gray, (left, ys[i], right, ys[i + 1]), depth + 1, out)


def _trim_white(im: Image.Image) -> Image.Image:
    mask = im.convert("L").point(lambda p: 255 if p < WHITE_THRESH else 0)
    bbox = mask.getbbox()
    return im.crop(bbox) if bbox else im


def split_composite(png_path: str | Path, workspace: str | Path, stem: str) -> list[Path]:
    """Split a composite figure into panel PNGs. Returns [] (no split) when it looks single-panel."""
    try:
        img = Image.open(str(png_path)).convert("RGB")
    except Exception:
        return []
    width, height = img.size
    if width < MIN_W or height < MIN_H:  # too small to be a real multi-panel figure
        return []

    boxes: list[tuple[int, int, int, int]] = []
    _split_box(img.convert("L"), (0, 0, width, height), 0, boxes)
    if len(boxes) <= 1:
        return []

    panels = [
        b for b in boxes if (b[2] - b[0]) >= MIN_PANEL_FRAC * width and (b[3] - b[1]) >= MIN_PANEL_FRAC * height
    ]
    if len(panels) <= 1:
        return []
    area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in panels)
    if area < MIN_AREA_FRAC * width * height:  # panels don't reconstruct the figure -> mis-detection
        return []

    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for j, box in enumerate(panels[:MAX_PANELS]):
        dst = workspace / f"{stem}_panel{j}.png"
        try:
            _trim_white(img.crop(box)).save(str(dst))
            out.append(dst)
        except Exception:
            continue
    return out if len(out) > 1 else []
