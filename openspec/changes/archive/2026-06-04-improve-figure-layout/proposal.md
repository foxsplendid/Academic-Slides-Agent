## Why

Figures look wrong on slides: the compiler splits the content area into **equal** horizontal slices
regardless of block type, and `render_figure` forces the picture to full content width with
auto-height — so a figure is cramped next to bullets, and tall/awkward-ratio figures overflow or
distort their slot. The reference 组会 deck makes figures large and keeps their aspect ratio.

## What Changes

- **Weighted block layout:** the content area is allocated by block weight (figure ≫ table > formula >
  bullets) instead of equal slices, so a figure slide gives the figure most of the room and the
  bullets a compact strip.
- **Aspect-preserving figure fit:** `render_figure` reads the image size and **fits it into its region
  (contain), centered**, instead of forcing full width — no overflow, no distortion. The figure's
  `caption` renders as a small centered line beneath it.

## Capabilities

### Modified Capabilities
- `pptx-compiler`: weighted per-block regions + aspect-preserving, centered figure rendering with a
  caption line.

## Non-goals

- Side-by-side image+text columns or multi-figure grids (single stacked region per block for now).
- Template-driven placeholders (still in-code layout).

## Impact

- `pptx_compiler/compiler.py` (weighted allocation) + `blocks.py` (`render_figure` contain-fit +
  caption). Uses Pillow (already required by python-pptx) to read image dimensions, guarded with a
  width-only fallback. Verified on the Zhang 2026 detailed deck.
