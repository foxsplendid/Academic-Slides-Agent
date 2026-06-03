## 1. Package setup

- [x] 1.1 Create `packages/core/formula/` package (`pyproject.toml`, `formula_render/`)
- [x] 1.2 Add `matplotlib` (BSD) dependency; record in `NOTICE`

## 2. Renderer

- [x] 2.1 Implement `MatplotlibFormulaRenderer.to_image(latex) -> Path | None` (Agg backend, high-DPI PNG, tight bbox)
- [x] 2.2 Return `None` on parse failure (so the compiler falls back to text)
- [x] 2.3 Cache by (latex, dpi, color) — render once, reuse

## 3. SPEC update

- [x] 3.1 Update `docs/SPEC.md` §6.2 (formula v1 = matplotlib PNG; MathJax/SVG deferred)
- [x] 3.2 Add a Changelog entry recording the approach change

## 4. Tests

- [x] 4.1 Parseable expression returns an existing image path
- [x] 4.2 Unparseable expression (mhchem) returns None
- [x] 4.3 Caching: same expression returns same path, not re-rendered
- [x] 4.4 Representative academic formulas (isotopes/subscripts/fractions/Greek) all render
- [x] 4.5 Integration: compiling a FormulaBlock with this renderer yields a picture shape
