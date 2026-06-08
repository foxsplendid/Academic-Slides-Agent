## Why

On a figure-heavy slide the figure (weight 3.2) crowded out co-located bullets (weight 1.0) — the
figure took ~76% of the content height, leaving text cramped and small (observed on a real deck).

## What Changes

- The compiler caps the **combined figure/chart/diagram height at 60%** of the content area **when
  bullets share the slide**, redistributing the remainder to the text block(s). A figure-only slide is
  unaffected (the cap applies only when bullets are present); tables are not treated as visual blocks.
- Extracted as a pure `_balanced_fractions(block_types)` helper for testability.

## Capabilities

### Modified Capabilities
- `pptx-compiler`: figure/chart/diagram height is capped when co-located with bullets.

## Impact

- `compiler.py` only. Verified by unit tests (figure capped to ≤0.6, bullets ≥0.4; figure-only
  unaffected; table not capped) and by re-rendering a real deck (cramped slides now legible).
