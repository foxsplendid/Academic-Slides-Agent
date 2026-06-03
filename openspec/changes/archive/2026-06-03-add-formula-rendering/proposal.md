## Why

Formulas currently degrade to plain text (the compiler's safe fallback). To deliver the
"hard science" promise, formula-worthy math must render as crisp images. This adds the first
real `FormulaRenderer` — MVP step 2 (docs/SPEC.md §10).

## What Changes

- Add `packages/core/formula/` — `MatplotlibFormulaRenderer` implementing the compiler's
  `FormulaRenderer` protocol (`to_image(latex) -> Path | None`):
  - Renders LaTeX math to a **high-DPI PNG** via matplotlib's `mathtext` (pure-Python, in-process).
  - Returns `None` for expressions mathtext cannot parse → the compiler falls back to editable text.
  - Caches by (latex, dpi, color) so repeated formulas are rendered once.
- **Update `docs/SPEC.md` §6.2 + Changelog**: formula v1 approach changes from "MathJax→SVG" to
  "matplotlib mathtext→PNG" — rationale: no Node subprocess, privacy-friendly in-process rendering,
  and python-pptx `add_picture` embeds PNG directly. A MathJax/SVG high-fidelity backend remains a
  pluggable later enhancement behind the same interface.

## Capabilities

### New Capabilities
- `formula-rendering`: render LaTeX math to an image for embedding, with a graceful `None`
  fallback, behind the compiler's `FormulaRenderer` interface.

### Modified Capabilities
<!-- pptx-compiler already consumes any FormulaRenderer structurally; no spec change there -->

## Non-goals

- MathJax/SVG high-fidelity backend (later enhancement).
- Native-editable OMML equations (SPEC v2).
- Chemistry/mhchem (`\ce{}`) — unsupported by mathtext → text fallback.

## Impact

- New package `packages/core/formula/`; new dependency **`matplotlib` (BSD)** — permissive, allowed.
- Integrates with `pptx-compiler` via a **structural Protocol** (no hard package dependency).
- Updates `docs/SPEC.md` (living constitution) per its maintenance rule.
