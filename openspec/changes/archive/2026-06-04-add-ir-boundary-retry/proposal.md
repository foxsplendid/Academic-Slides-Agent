## Why

Real models occasionally emit malformed output at the IR boundary — a dropped character
(`"lide_id"`), a wrong enum (`layout_type: "figure"`), or a stray fence — and today a single such
glitch raises `IRBoundaryError` and crashes the whole generation. These are transient, self-correcting
on a re-ask, so the planner should retry the parse a few times before giving up.

## What Changes

- `build_outline` retries on `IRBoundaryError`: it re-asks the LLM up to `max_attempts` times (default
  3), feeding the validation error back so the model returns corrected JSON. After the budget it
  re-raises the last error (a truly non-IR model still aborts before the compiler, as before).
- This is distinct from the critic loop: the critic re-plans a *valid* deck for content quality; this
  retry just gets a *parseable, schema-valid* deck at all.

## Capabilities

### Modified Capabilities
- `outline-agent`: tolerate transient malformed LLM output by retrying the IR boundary with the error
  fed back, bounded by `max_attempts`.

## Non-goals

- Retrying on a network/provider error (that is the provider's concern).
- Loosening the IR boundary itself — it stays strict; we only re-ask.

## Impact

- `outline.py` only (`build_outline` gains `max_attempts`; imports `IRBoundaryError`). No schema
  change. Existing behavior preserved: a valid deck parses on attempt 1 (no extra calls); a persistently
  non-IR model still raises.
