## Why

Dense academic bullets overflow the slide: the compiler renders at a fixed 16pt regardless of how much
text a region must hold, so long/many bullets spill off the slide. This is the most common 排版 failure.
Per SPEC §6.5, the deterministic primary is "measure, then place" (font metrics) — we add that.

## What Changes

- **Auto-fit bullet font**: `render_bullets` estimates the text's line count for its region (CJK-aware
  display width vs region width) and **shrinks the font** from a base size down to a floor until it
  fits, then renders at that size. Deterministic ("先量后排"), no rendering round-trip.

## Capabilities

### Modified Capabilities
- `pptx-compiler`: measure-then-place font fitting for bullet blocks (auto-shrink to avoid overflow).

## Non-goals

- Pagination / spill-to-continuation-slide (a structural change to slide count) — later. Per-character
  exact metrics (we use a CJK-aware estimate). Fitting non-bullet blocks.

## Impact

- `pptx_compiler/blocks.py` (`_fit_font` + `render_bullets`). No new deps, no IR change. Verified:
  a dense slide gets a smaller font than a sparse one and stays within its region budget.
