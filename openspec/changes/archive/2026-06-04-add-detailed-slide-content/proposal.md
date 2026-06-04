## Why

Even with clean MinerU evidence, the deck is too shallow for a real 组会 talk: one LLM call spreads
thin across the whole paper and emits ~3 generic bullets per slide. A talk needs per-slide depth —
actual method detail, the argument, and figure interpretation. Following PPTAgent's public two-stage
approach: plan a skeleton, then expand each slide **focused on its own evidence at full resolution**.

## What Changes

- New **two-stage planner** `build_deck_detailed` (`asa_agents/deepen.py`):
  1. **Skeleton:** one call yields a slide plan — `title`, `layout_type`, a one-line `focus`, the
     `evidence_pages` each slide draws on, and an optional `figure_id`.
  2. **Expand:** per slide, a focused call gets that slide's `focus` + the **full text of its
     evidence pages** (not the global truncated digest) + its figure caption, and returns one deep
     `SlideIR` slide (substantive bullets + interpretation + speaker notes). Slides are assembled and
     passed through the strict IR boundary.
- **Pluggable planner in the graph:** `build_graph(llm, *, planner=build_outline, ...)`. Default stays
  the single-shot `build_outline` (tests unchanged); the server wires `planner=build_deck_detailed`.
- Per-call resilience reuses the IR-boundary retry pattern.

## Capabilities

### Modified Capabilities
- `outline-agent`: add a two-stage detailed deck builder (skeleton → per-slide focused expansion).
- `orchestration`: the graph's planner is injectable so the detailed builder can drive real runs.

## Non-goals

- Parallelizing the per-slide calls, or re-expanding only the slides the critic flagged (today a retry
  re-runs the whole two-stage). Both are later optimizations.

## Impact

- New `asa_agents/deepen.py`; `graph.py` gains a `planner` parameter; `server.py` uses the detailed
  planner. Single-shot `build_outline` and all existing tests stay as-is. Verified on Zhang 2026
  (MinerU evidence) — deeper per-slide content than the single-shot deck.
