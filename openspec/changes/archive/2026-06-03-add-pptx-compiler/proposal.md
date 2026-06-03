## Why

The compiler is the project's moat and its biggest risk: turning Slide-IR into a **native,
editable `.pptx`** (real tables and text, not page images) with **no AI**. Proving this first
(MVP step 1, docs/SPEC.md §10) de-risks the hardest, most defensible capability before any
agent work.

## What Changes

- Add `packages/core/compiler/` — a deterministic, AI-free `Deck` → `.pptx` compiler over `slide-ir`:
  - `compile_deck(deck, out_path, *, template=None, formula_renderer=None) -> Path`.
  - Render each `layout_type` (title, section, bullet_evidence, two_column_table, formula_banner, figure_caption) into native python-pptx objects via **explicit positioning**.
  - Render blocks: `TableBlock` → **native table**; `BulletBlock` → **native text**; `FigureBlock` → picture (best-effort) or placeholder; `FormulaBlock` → image via an **injectable formula renderer**, falling back to LaTeX-as-text.
  - `FormulaRenderer` Protocol + `NullFormulaRenderer` (text fallback); the real SVG renderer arrives in `add-formula-svg`.
  - A small CLI (`python -m pptx_compiler <deck.json> <out.pptx>`) and a committed `examples/sample_deck.json`.
- Support **template theme inheritance**: when a `.pptx` template is supplied, use it as the base presentation (theme/fonts/slide-size inherited).

## Capabilities

### New Capabilities
- `pptx-compiler`: the deterministic engine that renders a validated `Deck` into a native,
  editable `.pptx`. The single rendering authority; the LLM never touches pptx.

### Modified Capabilities
<!-- none — `slide-ir` is consumed, not modified -->

## Non-goals

- Formula **image** rendering (LaTeX→SVG/OMML) — separate change `add-formula-svg`.
- Evidence-Pool asset resolution for figures — separate change.
- Full Template Manifest tokenization + capability matching — separate change `add-template-mapper`.
- Deep overflow/overlap handling — basic word-wrap only here (full detection is later).

## Impact

- New package `packages/core/compiler/`; depends on **`python-pptx` (MIT)** and `asa-slide-ir` (local).
- No AGPL/GPL introduced. No AI/runtime-model dependency.
