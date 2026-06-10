## Why

Two blind-gate rounds showed the durable Design gap comes from per-page information design (card
groups, annotated comparisons, bespoke data graphics) that the closed block vocabulary cannot
express. Path B was triggered by the pre-agreed criterion. The vendored MIT svg2pptx engine (B-(a))
makes a constrained-SVG escape hatch cheap and keeps the native-editable hard constraint.

## What Changes

- **CanvasBlock + LayoutType.CANVAS** (premium tier): a full-page constrained SVG composition
  (viewBox 0 0 1280 720).
- **Canvas guard** (`validate_canvas_svg`): bans script/foreignObject/animation/iframe/media/image,
  external hrefs, script-handler attributes, external url() styles; requires the canonical viewBox;
  300k size cap. Enforced at three points: expansion retry loop, critic (repair-routable), compile.
- **Injection pipeline**: compiled deck -> vendored finalize repair passes (entities, tspan flatten,
  text merge/reflow, rect->path) -> svg2pptx conversion -> slide XML swapped into the saved package
  (vector+text only, rels untouched). Fail-open at every stage; geometry lint skips canvas pages.
- **Premium generation**: job option `premium` -> skeleton may plan 2-3 canvas pages for the most
  valuable results/mechanism slides; canvas plans expand under a dedicated authoring system prompt
  (palette/font/geometry contract, evidence-only numbers) with guard-validated retries and a
  bullet-page fallback; UI exposes a 精品档 toggle.

## Capabilities

### Modified Capabilities
- `slide-ir`, `pptx-compiler`, `outline-agent`: as above.

## Impact

234 tests green (guard bans, editable injection, invalid-canvas fail-open, premium routing,
degradation). Real-LLM smoke: DeepSeek authored a forest-plot comparison + stat card + mini scatter
page, guard-clean first try, 40 editable text shapes after conversion. The LLM-never-writes-
coordinates principle is now scoped to the FAST tier; the premium tier trades it for expressiveness
behind the guard + deterministic repair + visual QA.
