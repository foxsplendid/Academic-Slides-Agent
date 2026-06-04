## Why

A good 组会 deck doesn't just quote numbers — it visualizes them. The user's reference decks include
charts built from the paper's data. We want the same, but **native** (per our core principle): real,
double-click-editable PowerPoint charts, not images.

## What Changes

- **New `ChartBlock` in Slide-IR** (`chart_type` ∈ bar/line/scatter/pie, `categories`, `series` of
  `{name, values, x?}`, optional `title`). Added to the block union; the LLM may emit it like any block.
- **Native chart rendering** in the compiler via `python-pptx` `add_chart` (CategoryChartData for
  bar/line/pie, XyChartData for scatter) — fully editable in PowerPoint. Series are padded/truncated to
  the category count defensively.
- **Planner awareness:** the two-stage expand prompt (and single-shot prompt) describe `ChartBlock`
  and when to use it — **only from quantitative data that appears in the evidence; never fabricate
  numbers** (anti-hallucination, SPEC core).

## Capabilities

### Modified Capabilities
- `slide-ir`: add the `ChartBlock` (+ `ChartSeries`) block type to the locked vocabulary.
- `pptx-compiler`: render native charts; weight charts above text in the layout.
- `outline-agent`: emit charts from evidence data, with a no-fabrication rule.

## Non-goals

- Combo/stacked/area charts, dual axes, error bars (v1 = bar/line/scatter/pie).
- Auto-deciding chart type from raw tables without the LLM; the planner chooses.

## Impact

- `slide_ir/models.py` (+ schema export), `pptx_compiler` (`blocks.render_chart` + wiring + weight),
  `asa_agents` prompts. No new deps (python-pptx already bundles chart support). Verified: a crafted
  chart deck renders native charts; planner can emit a chart on real evidence.
