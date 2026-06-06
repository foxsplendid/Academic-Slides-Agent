## Why

Formula v1 (matplotlib mathtext) covers only a subset of LaTeX math — **chemistry (mhchem),
matrices, and alignment fall back to text**, a real sore for science talks. Batch 3 adds a
high-fidelity backend behind the same `FormulaRenderer` interface.

## What Changes

- **MathJax(+mhchem) Node sidecar** (`packages/core/formula/node/sidecar.js`): LaTeX → MathJax SVG →
  resvg PNG. Covers full LaTeX, chemistry, matrices. **Arms-length subprocess** (MathJax Apache-2.0,
  resvg MPL-2.0 — neither links our Apache Python).
- **`MathJaxFormulaRenderer`** (Python): calls the sidecar, caches by hash; `available()` gates on
  Node + installed sidecar `node_modules` (optional — falls back if absent).
- **`AutoFormulaRenderer`** (tier): simple math → matplotlib (fast, no Node); advanced (chemistry/
  matrices) → MathJax if available; the other as fallback. `default_formula_renderer()` enables the
  MathJax tier only when the sidecar is present. The server wires it.

## Capabilities

### Modified Capabilities
- `formula-rendering`: add a MathJax sidecar backend + a tiered auto-renderer (chemistry/matrices now
  render natively instead of falling back to text).

## Non-goals

- Native editable OMML equations (still v2). Bundling Node/node_modules (the sidecar is opt-in via
  `npm install`). Server-side LaTeX install.

## Impact

- New `node/` sidecar (package.json + sidecar.js; `node_modules` gitignored), `mathjax_renderer.py`,
  `auto_renderer.py`; `formula_render/__init__` exports; `server.py` uses `default_formula_renderer()`.
  NOTICE gains MathJax + resvg (Node-side, optional). Verified: chemistry/matrix/isotope formulas
  render to PNG; tier routes correctly.
