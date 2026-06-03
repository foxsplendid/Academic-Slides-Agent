## 1. Package setup

- [x] 1.1 Create `packages/core/compiler/` package (`pyproject.toml`, `pptx_compiler/`)
- [x] 1.2 Declare deps: `python-pptx>=1.0` (MIT) + `asa-slide-ir` (local via `tool.uv.sources`); record in `NOTICE`

## 2. Formula renderer abstraction

- [x] 2.1 Define `FormulaRenderer` Protocol (`to_image(latex) -> Path | None`)
- [x] 2.2 Implement `NullFormulaRenderer` (returns None → text fallback)

## 3. Block rendering

- [x] 3.1 `render_table` → native python-pptx table (header row + data rows)
- [x] 3.2 `render_bullets` → text frame, one paragraph per item
- [x] 3.3 `render_formula` → picture if renderer yields an image, else LaTeX-as-text
- [x] 3.4 `render_figure` → picture if asset path exists, else placeholder text

## 4. Slide & deck compilation

- [x] 4.1 Per-`layout_type` slide rendering (title/section/bullet_evidence/two_column_table/formula_banner/figure_caption) via explicit positioning
- [x] 4.2 `compile_deck(deck, out_path, *, template=None, formula_renderer=None) -> Path`
- [x] 4.3 Template theme inheritance (use supplied `.pptx` as base presentation)

## 5. CLI & example

- [x] 5.1 `python -m pptx_compiler <deck.json> <out.pptx>` entry point
- [x] 5.2 Commit `examples/sample_deck.json` (title + bullets + table + formula)

## 6. Tests

- [x] 6.1 N slides for a deck of N; output reopens as valid PPTX
- [x] 6.2 TableBlock → native table shape with C cols and R+1 rows
- [x] 6.3 BulletBlock → text frame containing all items
- [x] 6.4 FormulaBlock → LaTeX text under null renderer; picture under an image renderer
- [x] 6.5 Template slide size is inherited
- [x] 6.6 Determinism: same deck → identical slide count + per-slide shape-type sequence
