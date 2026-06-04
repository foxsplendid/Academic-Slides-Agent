## 1. Weighted layout

- [x] 1.1 `_render_slide`: allocate per-block height by weight (figure ≫ table > formula > bullets)

## 2. Aspect-preserving figure

- [x] 2.1 `render_figure`: read image size (Pillow), contain-fit into region, center; width-only fallback
- [x] 2.2 Render the figure `caption` as a small centered line beneath the image

## 3. Tests & verify

- [x] 3.1 Unit: a figure fits within its region (picture width ≤ content width, height ≤ region) and is centered
- [x] 3.2 Unit: figure slide gives the figure more height than an equal split would
- [x] 3.3 Real: recompile Zhang 2026 detailed deck — figures larger, aspect preserved; full suite green
