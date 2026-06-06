## Why

Three quick robustness/quality fixes (enhancement batch 1):
- The critic false-flags chart/diagram slides that use the `two_column_table` layout ("no table
  block"), triggering wasteful re-plans.
- LangGraph warns it will (in a future version) **block** deserializing our checkpointed `slide_ir`
  types on resume — a latent break of the Hard-Stop resume feature.
- The per-slide "→ interpretation" line is requested but not enforced, so it's inconsistent.

## What Changes

- **Critic relax**: the `two_column_table` consistency check is satisfied by a `table` **or** `chart`
  **or** `diagram` block (all are structured/data blocks).
- **msgpack allowlist**: the default graph checkpointer registers all `slide_ir.models` enum/model
  types via `JsonPlusSerializer(allowed_msgpack_modules=…)`, silencing the warning **and** preventing
  the future hard-block (verified resume still works, 0 warnings). Collected programmatically so new
  block types are auto-included.
- **Interpretation enforced**: the expand prompt makes the final "→ …" interpretation bullet mandatory.

## Capabilities

### Modified Capabilities
- `critic`: `two_column_table` accepts table/chart/diagram.
- `orchestration`: checkpointer registers `slide_ir` types (resume-safe, no msgpack warning).
- `outline-agent`: the per-slide interpretation line is required.

## Non-goals

- Adding dedicated `data_chart` / `diagram` layout types (we relax the existing check instead).

## Impact

- `critic.py` (one condition), `graph.py` (checkpointer serde helper), `deepen.py` (prompt). No new
  deps, no IR change.
