## Why

Research + line-level audit showed our decks look mediocre for compiler reasons, not IR reasons: the
compiler had exactly TWO arrangements (centered divider; title + full-width vertical stack), 4 of 6
LayoutTypes rendered identically, charts/tables were raw Office defaults, and there was zero theme
chrome. Academic evidence (PPTAgent EMNLP'25, LayoutNUWA, AutoPresent) supports constrained layout
vocabularies + inherited design — the IR is the right architecture; the vocabulary was missing.

## What Changes

- **Layout v2 (multi-region templates)**: the compiler gains a region-template table —
  `figure_caption` = figure RIGHT / text LEFT (58/42), new `figure_left` mirror, `two_column_table` =
  major block LEFT / takeaways RIGHT, new `two_content` (50/50), new `figure_grid` (2-4 figures:
  1x2 / 1x3 / 2x2, optional bottom text strip), new `big_figure` (dominant figure + optional strip),
  `formula_banner` = formula band (32%) + support text. Strict composition matching; unmatched
  compositions degrade to the weighted vertical stack. Generic side-by-side heuristic also upgrades
  any 2-block [major + bullets] slide. Figures now center vertically in their region.
- **Data graphics v1**: charts styled from StyleProfile tokens (6-color `chart_palette`, axis/legend
  fonts at `chart_axis_pt`, data labels on small single-series bar/pie, bottom legend, gap_width 60,
  light gridlines, per-slice pie colors). Tables get header-row fill (`table_header_rgb`) + white bold
  header text + zebra banding (`table_band_rgb`); `TableBlock.highlight` is now implemented
  ({"cells": [[row, col]]} -> bold emphasis-colored cells).
- **Theme v1 (deck chrome)**: `accent_rgb`/`accent_bar`/`page_numbers`/`muted_rgb` tokens; content
  slides get a short accent rule under the title + page number; cover/section get a centered accent
  rule; covers carry no page number.
- **Planner vocabulary**: SKELETON prompt now offers the full 10-layout vocabulary with usage guidance
  (alternate figure_caption/figure_left; figure_grid for subpanel comparisons; big_figure for key
  results). Critic checks figure-led layouts carry a figure block.

## Capabilities

### Modified Capabilities
- `slide-ir`: 4 new LayoutType values (figure_left, two_content, figure_grid, big_figure).
- `pptx-compiler`: region templates, styled charts/tables, theme chrome, vertical figure centering.
- `outline-agent`: layout vocabulary in the skeleton prompt.
- `critic`: figure-led layout consistency checks.

## Impact

Verified by 19 new unit tests (region geometry, palette/labels/legend, header fill/banding/highlight,
chrome presence) + full suite green + a real-deck recompile visually confirming side-by-side figure
slides, styled table, accent bars, page numbers. Old deck.json files compile to the improved look with
no regeneration (composition-based matching).
