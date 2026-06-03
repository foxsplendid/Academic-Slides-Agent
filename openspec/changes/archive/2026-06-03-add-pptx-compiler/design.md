## Context

`slide-ir` (now in `openspec/specs/slide-ir/`) defines the validated contract. This change adds
the **deterministic renderer** that consumes it. Per docs/SPEC.md §3.1, the compiler is AI-free:
same IR in → same pptx out. It is the credibility-defining "native editable" capability (§10).

## Goals / Non-Goals

**Goals:**
- A pure function `compile_deck(deck, out_path, *, template, formula_renderer) -> Path`.
- Native python-pptx objects: real tables, real text frames.
- Pluggable formula rendering with a safe text fallback (decouples from `add-formula-svg`).
- Template **theme inheritance** by using a supplied `.pptx` as the base presentation.

**Non-Goals:**
- Formula image rendering; figure asset resolution; full Template Manifest/capability matching;
  deep overflow detection (basic word-wrap only).

## Decisions

- **Explicit positioning (not placeholder indices) for v1.** Placeholder layouts vary per
  template; computing shape positions from slide width/height is deterministic and
  template-agnostic. Placeholder/Manifest mapping is the later `add-template-mapper` change.
- **Native `add_table` for tables** — the whole point ("editable, not images"). Header row
  styled; cells filled from `columns`/`rows`.
- **`FormulaRenderer` Protocol + `NullFormulaRenderer`** — the compiler asks a renderer for an
  image and falls back to LaTeX text. This keeps the compiler shippable now and lets
  `add-formula-svg` plug in an `SvgFormulaRenderer` later without touching the compiler.
- **Template = base `Presentation(template_path)`** — output inherits theme/fonts/size even
  though shapes are added explicitly. Full placeholder mapping deferred.
- **`python-pptx` (MIT)** — the only new runtime dependency; matches the SPEC stack.

## Risks / Trade-offs

- [Explicit positioning looks less "designed" than placeholder layouts] → acceptable for MVP;
  `add-template-mapper` will bind to real placeholders for polish.
- [Long content overflows fixed boxes] → enable word-wrap + simple auto-fit now; real
  measure→shrink→spill is a later change (docs/SPEC.md §6.5).
- [pptx zip is not byte-deterministic (timestamps)] → assert determinism at the *structural*
  level (slide count + per-slide shape-type sequence), not byte equality.
