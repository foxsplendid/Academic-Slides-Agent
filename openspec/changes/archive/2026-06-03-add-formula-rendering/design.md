## Context

The compiler renders `FormulaBlock` via an injectable `FormulaRenderer`, defaulting to a text
fallback (`NullFormulaRenderer`). This change provides the first real renderer. docs/SPEC.md §6.2
originally specified MathJax→SVG; this design revises that decision and updates the SPEC.

## Goals / Non-Goals

**Goals:**
- A pure-Python, in-process renderer: `to_image(latex) -> Path | None`.
- Crisp output embeddable by python-pptx `add_picture`.
- Graceful `None` on unparseable input; caching.

**Non-Goals:**
- MathJax/SVG backend; OMML; chemistry/mhchem.

## Decisions

- **matplotlib `mathtext` → PNG** (chosen) vs **MathJax/Node → SVG** (SPEC original) vs
  **external service (CodeCogs)**:
  - MathJax/Node — high fidelity (mhchem) but needs a Node subprocess + npm; heavier MVP.
  - External service — leaks unpublished formulas off-host (privacy) and adds a network dep.
  - **matplotlib** — pure-Python, in-process (privacy), BSD, covers core academic math, and
    python-pptx embeds PNG directly. Unparseable input degrades to text via the existing
    fallback. Chosen for MVP; MathJax/SVG remains a pluggable backend behind the same interface.
- **PNG, not SVG** — python-pptx `add_picture` does not embed SVG directly; high-DPI PNG is crisp
  enough for slides and works today.
- **Structural Protocol** — the renderer matches `FormulaRenderer` by shape; the formula package
  does not import the compiler (low coupling).
- **Cache key = (latex, dpi, color)** — repeated formulas render once.

## Risks / Trade-offs

- [mathtext supports only a subset of LaTeX] → return None → text fallback; document the limit;
  add a MathJax backend later for full fidelity (e.g. mhchem).
- [matplotlib is a heavy dependency] → acceptable for a core feature; isolated in its own package.
- [PNG is not vector] → 300 DPI is crisp for slides; true SVG/EMF is a later enhancement.
