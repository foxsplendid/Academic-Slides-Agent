## Why

Real runs showed two recurring defects: (1) the skeleton occasionally produced two near-duplicate
slides (same point/chart), and (2) the model sometimes used a `section` divider layout for slides that
actually carry content. The critic retry loop can only *repair* a slide in place — it can never *delete*
one — so redundancy must be removed deterministically.

## What Changes

- **Deterministic dedup (`_dedup_plans`)** in the skeleton, before expansion: char-level
  `difflib.SequenceMatcher` on normalized title+focus (CJK-safe), keep the first of each near-duplicate
  cluster (ratio ≥ 0.86). Removes redundancy *and* saves an expansion call.
- **Deterministic layout backstop (`_fix_structural_layout`)** at assembly: a `title`/`section` divider
  carrying any content block is relayout to `bullet_evidence` (applied to expanded and repaired slides).
- **Prompt rules**: SKELETON/EXPAND now forbid two slides on the same point and clarify that
  `title`/`section` are dividers with no content blocks.
- **Critic backstops**: a divider-with-content finding is repair-routable (`slide '<id>'`, relayout in
  place); a near-duplicate-title finding is deliberately *not* repair-routable (reaches the human at the
  Hard-Stop instead of looping the in-place repair).

## Capabilities

### Modified Capabilities
- `outline-agent`: deterministic skeleton dedup + structural-layout backstop + prompt rules.
- `critic`: divider-with-content and near-duplicate-title checks.

## Impact

- `deepen.py`, `critic.py`. Verified: near-dup plans collapse (dropped one never expanded); distinct
  titles preserved; section+content relayout to bullets; real dividers untouched; duplicate-title
  finding is non-repair-routable. Full suite green.
