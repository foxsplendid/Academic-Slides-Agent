## Context

`GenerationState` was pre-fitted with `critic_findings`, `retry_count`, `max_retries`, and
`Phase.CRITIQUING` (see `slide_ir/models.py`) precisely so this loop could land without a state
migration. This change fills them in.

## Where the critic runs: before the Hard-Stop

The critic runs **between `plan` and `approval`**, not after `compile`. Rationale:

- The human's Hard-Stop is the expensive, attention-scarce step. They should review a *corrected*
  outline, not a draft full of mechanical defects.
- All v1 checks are knowable from the IR alone (counts, lengths, reference existence) — no rendering
  needed. Pixel-level overflow (which needs layout) is explicitly a v2 VLM concern (SPEC §6).

## Loop shape and termination

```
START -> plan -> critic -> (router)
                              ├─ findings && retry_count < max_retries -> plan   (retry)
                              └─ else -> approval -> compile -> END
```

- `critic` overwrites `critic_findings` each pass (fresh measurement) and sets `phase=CRITIQUING`.
- The **router** is a pure function reading the latest `critic_findings` and `retry_count`.
- `plan` increments `retry_count` when it consumes feedback (`critic_findings` non-empty on entry),
  so the counter advances exactly on retries. With `max_retries=2` the planner runs at most 3 times
  (1 initial + 2 retries), then `approval` proceeds **best-effort** with the residual findings left in
  state for transparency (surfaced to the user / speaker notes).

This guarantees termination (monotonic counter, hard ceiling) and never silently drops a deck — a
deck that still has findings after the budget is exhausted still goes to the human, who is the final
authority at the Hard-Stop.

## Critic checks (v1, deterministic)

| Check | Heuristic (measure, then flag) |
|---|---|
| Empty content slide | non-`title`/`section` slide with zero blocks |
| Empty title | content slide with blank `title` |
| Title overflow | `len(title) > 100` |
| Bullet overflow | a `bullets` block with `> 7` items, or any item `> 200` chars |
| Table overflow | `> 6` columns or `> 12` rows |
| Layout/block mismatch | `formula_banner` w/o formula, `two_column_table` w/o table, `figure_caption` w/o figure |
| Dangling figure | `figure.asset_id` not in the Evidence Pool asset ids |

Thresholds live as module constants so a later change can tune them without touching the loop. They
are intentionally conservative — the critic flags, the LLM (or human) fixes.

## Why feedback, not auto-edit

The critic could mechanically trim bullets itself, but that risks dropping scientific content. Instead
it reports and lets the planner LLM re-author with the findings in context (PaperFit-style compile
feedback). Only the human-at-Hard-Stop and the LLM change content; the critic stays read-only.
