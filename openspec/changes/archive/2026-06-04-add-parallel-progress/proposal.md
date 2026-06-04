## Why

Two pains: (1) the two-stage builder expands slides **serially** (~11 sequential LLM calls ≈ 2 min)
even though each slide is independent; (2) the UI shows almost no progress — the whole expansion runs
inside one graph node, so the user stares at a spinner with no idea which step/slide is in flight.

## What Changes

- **Parallel per-slide expansion (default):** `build_deck_detailed` expands slides concurrently with a
  thread pool (LLM calls are I/O-bound). On any worker failure it **falls back to serial** so a flaky
  parallel run never breaks generation.
- **Fine-grained progress:** the builder accepts a `progress` callback and reports `skeleton`,
  `slide done/total`, etc. The graph `plan` node wires that callback to LangGraph's custom stream
  writer, and the SSE endpoint emits `progress` events alongside node updates.
- **Frontend status panel:** a phase stepper (parse → outline → generating N/total → review → compile →
  done) with the live slide counter, replacing the bare log — modeled on PPTAgent's progress display.

## Capabilities

### Modified Capabilities
- `outline-agent`: parallel slide expansion with serial fallback + a progress callback.
- `web-ui`: a phase/slide progress panel driven by new `progress` SSE events.

## Non-goals

- Per-slide LangGraph nodes / map-reduce (the dynamic-N restructure); a callback + custom stream is
  enough. Re-expanding only failed slides (today the fallback re-runs all serially).

## Impact

- `deepen.py` (thread pool + progress), `outline.py` (`progress=None` no-op to match the planner
  signature), `graph.py` (wire `get_stream_writer`), `app.py` (`stream_mode=["updates","custom"]` +
  `progress` events), `apps/web` (`api.ts` + `App.tsx` + styles). Verified on Zhang 2026: faster
  generation + live per-slide progress.
