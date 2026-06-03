## Why

The graph runs `plan -> approval -> compile` once and trusts the LLM's first draft. Real decks come
back with overflowing bullets, empty slides, layout/block mismatches, and figures that reference
assets not in the Evidence Pool. We need a **deterministic, AI-free critic** that measures the IR and
a **bounded retry loop** that feeds findings back to the planner — so the human reviews a
self-corrected outline at the Hard-Stop, not the raw first draft.

## What Changes

- New **`critic`** capability: `critique_deck(slides, evidence) -> list[str]`, a pure function that
  measures the Slide-IR and returns human-readable findings. Checks (all deterministic, "先量后排"):
  empty/oversized titles, empty content slides, over-long bullet lists, over-large tables,
  layout↔block mismatches (e.g. `formula_banner` with no formula), and dangling `figure.asset_id`
  not present in the Evidence Pool (anti-hallucination).
- **Retry loop in the graph**: `plan -> critic -> {findings & retries left -> plan, else -> approval}`.
  The critic runs **before** the Hard-Stop, so the human approves a corrected outline. Re-planning
  passes the findings back as `feedback` so the LLM fixes them. Bounded by `max_retries` (default 2).
- `build_outline(..., feedback=...)` appends prior findings to the prompt.

## Capabilities

### New Capabilities
- `critic`: a deterministic deck critic plus a bounded plan↔critic retry loop that self-corrects the
  outline before the human Hard-Stop.

### Modified Capabilities
<!-- orchestration: inserts a critic node + conditional retry edge between plan and approval -->
<!-- outline-agent: build_outline gains an optional feedback argument -->

## Non-goals

- VLM / pixel-accurate visual critique (post-compile, v2). v1 measures the IR, not rendered pixels.
- LLM-based critique. The critic is AI-free and deterministic for reproducibility and zero cost.

## Impact

- `asa_agents` gains `critic.py`; `graph.py` adds a node + conditional edge; `outline.py` gains a
  `feedback` arg. No new third-party dependencies. `GenerationState` already carries
  `critic_findings`/`retry_count`/`max_retries` (no schema change).
