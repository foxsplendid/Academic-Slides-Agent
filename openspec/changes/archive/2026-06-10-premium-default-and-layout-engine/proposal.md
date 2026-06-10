## Why

User mandate: output quality first, no sacred rules. Three levers were approved after the Path-B
review — make the premium canvas tier the default quality path, give it a deterministic geometry
floor, and feed it the MIT composition exemplars. Separately, the recurring "layout template"
complaints (compositions with no matching mold collapsing into a cramped vertical stack) needed a
structural fix, not another enumerated template.

## What Changes

- **Premium default ON** (graph/API/frontend): the skeleton decides per page between canvas free
  composition (key results/mechanism/comparison pages) and deterministic blocks; the blocks path
  remains the fallback and the quality floor.
- **Canvas geometry lint** (`lint_canvas_svg`): deterministic text-overflow and text-overlap
  estimation in SVG space; wired into the authoring retry loop and the critic.
- **Composition exemplars**: 12 full-page SVG exemplars vendored from the MIT snapshot
  (canvas_exemplars/, NOTICE updated); a keyword router injects ONE matching exemplar into the
  canvas prompt as a style reference (colors/data overridden by the contract).
- **General layout compositor** replaces the strict template matcher's fallback: any mix of majors
  (figure/chart/diagram/table), bullets, one stat band (top) and one callout band (bottom) now gets
  a designed arrangement — single major side-by-side with text, multiple majors gridded with text
  below, twin bullet lists as columns. The "no template matched -> vertical stack" failure class is
  gone; only exotic mixes still stack.

## Capabilities

### Modified Capabilities
- `pptx-compiler`: general compositor; canvas geometry lint.
- `outline-agent`: premium default; exemplar injection.

## Impact

241 tests green. Real-LLM smoke (exemplar-guided): scatter + 1:1 line + axis ticks + winner-row
comparison table + diagnostics card, guard and geometry lint clean on the first attempt, fully
editable after conversion.
