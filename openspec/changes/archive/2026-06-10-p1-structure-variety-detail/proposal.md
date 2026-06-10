## Why

P1 wave of paper-ppt-agent-inspired improvements (methodology only): decks lacked the full academic
narrative chrome (no TOC/ending), layout assignment had no deck-level variety planning (stamped-out
runs of one layout), density was one-size-fits-all, and chart-type selection lacked a taxonomy.

## What Changes

- **Structure pages**: `toc` (numbered accent-chip agenda rendered deterministically) and `ending`
  (designed closing divider) LayoutTypes; skeleton plans cover→toc→sections→ending; ending joins the
  structural sets; critic checks toc carries its agenda bullets.
- **Layout variety**: skeleton prompt treats per-slide layout assignment as a deck-level design
  decision (alternate figure sides, big_figure for the key result, ban on 4+ same-layout runs); critic
  adds a deterministic monotony check (>3 consecutive content slides sharing one layout → repair-
  routable finding; dividers/TOC reset the run).
- **Detail levels**: quantified `DETAIL_PROFILES` (brief 6-8 pages / normal 8-12 / high 12-16 with
  bullet+notes quotas) injected into skeleton+expand prompts; `detail` rides job options end to end
  (upload form → GenerationState → planner kwarg); frontend gains a 详细程度 select.
- **Chart taxonomy**: expansion prompt gets explicit selection guidance (comparison→bar, trend→line,
  composition→pie, correlation→scatter).

## Capabilities

### Modified Capabilities
- `slide-ir`: toc + ending layouts.
- `pptx-compiler`: TOC agenda + ending renderers.
- `outline-agent`: variety planning, detail profiles, chart taxonomy.
- `critic`: layout-monotony + toc-consistency checks.

## Impact

10 new tests; suite green; structural pages visually verified via real render. Note: the planner
fixture keys on the substring "一页" — prompt wording must avoid it outside the expansion system
(hit twice now; documented in the prompt-edit history).
