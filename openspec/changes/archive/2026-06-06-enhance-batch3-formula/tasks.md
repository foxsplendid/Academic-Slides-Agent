## 1. Node sidecar

- [x] 1.1 `node/package.json` (mathjax-full + @resvg/resvg-js) + `node/sidecar.js` (LaTeX→MathJax SVG→resvg PNG, mhchem)
- [x] 1.2 Verify: chemistry/matrix/isotope render to PNG

## 2. Python backend + tier

- [x] 2.1 `MathJaxFormulaRenderer` (subprocess + cache + `available()`)
- [x] 2.2 `AutoFormulaRenderer` (simple→matplotlib, advanced→MathJax) + `default_formula_renderer()`
- [x] 2.3 Server uses `default_formula_renderer()`; NOTICE + node_modules gitignored

## 3. Tests & verify

- [x] 3.1 Unit: `is_advanced` detection; Auto routes advanced→MathJax / simple→matplotlib
- [x] 3.2 Unit: MathJax renders chemistry (skipped if sidecar not installed)
- [x] 3.3 Full suite green
