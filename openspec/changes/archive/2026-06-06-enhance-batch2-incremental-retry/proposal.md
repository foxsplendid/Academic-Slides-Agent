## Why

When the critic finds defects, the graph re-runs the **whole** two-stage builder (skeleton + every
slide), even though usually only one or two slides are flagged — wasting LLM calls and time. Retries
should be incremental: fix only the flagged slides, keep the rest.

## What Changes

- **Incremental repair in `build_deck_detailed`**: given the prior slides + the critic feedback, it
  re-calls the LLM **only for the flagged slide ids** (a focused "fix this slide given the finding"
  pass that preserves the slide's topic/evidence) and keeps the good slides untouched — skipping the
  skeleton call and all good-slide expansions.
- The graph's plan node passes `prior_slides` on a retry; `build_outline` accepts (and ignores) it for
  planner-signature parity.

## Capabilities

### Modified Capabilities
- `outline-agent`: on a critic retry, the two-stage builder repairs only the flagged slides.

## Non-goals

- Speeding up the *initial* generation (separate concern). Re-running the skeleton on retry.

## Impact

- `deepen.py` (`_repair_slide` + repair branch + `prior_slides`), `outline.py` (`prior_slides` no-op),
  `graph.py` (pass `prior_slides`). No IR change. Verified: a one-slide defect re-calls the LLM once,
  not N+1 times.
