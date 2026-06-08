## Why

Formulas currently render to PNG (matplotlib / MathJax). The "native-editable" core principle wants
real, editable PowerPoint equations (OMML). The robust general path is blocked: the forward
MathML→OMML stylesheet (`MML2OMML.XSL`) is proprietary Microsoft (only the *reverse* TEI `omml2mml.xsl`
is open-licensed), and python-pptx native-equation injection is known to be unreliable. So full OMML —
chemistry, matrices, verified PowerPoint rendering — stays a v2 item (it would use arms-length
Pandoc/`texmath`). This change ships the safe, license-clean increment.

## What Changes

- **Clean-room `latex_to_omml`** (no proprietary XSLT): a from-scratch LaTeX→OMML converter for the
  common subset — identifiers, sub/superscripts, fractions, roots, Greek, common operators. It is
  **conservative**: anything it can't convert confidently returns `None` (→ image fallback); it never
  emits partial/malformed OMML.
- **Opt-in renderer tier**: `AutoFormulaRenderer(native_omml=…)` exposes `to_omml(latex)`; enabled via
  `ASA_NATIVE_FORMULA` (default **off**).
- **Safe compiler embedding**: when the renderer yields OMML, the compiler injects an editable equation
  wrapped in `mc:AlternateContent` with an `<a14:m>` choice and a **LaTeX-text `mc:Fallback`**, so a
  reader ignoring the extension degrades to text — it can never produce a blank/corrupt slide. Any
  failure falls through to the existing image tier.

## Capabilities

### Modified Capabilities
- `formula-rendering`: optional native-editable OMML tier for the simple subset, with image fallback.

## Non-goals (deferred to v2)

- Chemistry (`\ce`), matrices/environments, integrals/sums-with-limits; **verification that the embedded
  OMML renders in real PowerPoint** (the image tier remains the production default until confirmed).

## Impact

- New `formula_render/latex_omml.py`; `auto_renderer.py` gains `to_omml`; `blocks.py` gains a
  fallback-protected native-equation path. Default behavior unchanged (opt-in). Verified: converter
  well-formedness + conservative `None`; OMML survives python-pptx save+reopen with text fallback;
  unsupported input falls back to image. Full suite green.
