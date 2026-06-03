## Why

Everything in Academic-Slides-Agent depends on one foundational contract: the **Slide-IR**.
It is the only thing the LLM is allowed to produce and the only input the deterministic
compiler consumes. Defining it first locks the LLM boundary, decouples content from
rendering, and unblocks the compiler, agents, and frontend to proceed in parallel.

## What Changes

- Add `packages/core/ir/` — the canonical Slide-IR data contract (Pydantic v2):
  - `SlideIR` with a **closed `layout_type` vocabulary** and a list of typed `blocks`.
  - Content blocks as a **discriminated union** on `type`: `formula`, `table`, `bullets`, `figure`.
  - `EvidenceAsset` (Evidence Pool item with provenance) and `GenerationState` (workflow state).
- Add **validation** that rejects malformed IR (table without `columns`, formula without `latex`, unknown types).
- Add **JSON Schema export** so the frontend can generate matching TypeScript types.
- Add a unit-test suite: valid/invalid fixtures + round-trip (model → JSON → model).
- No runtime AI and no rendering in this layer.

## Capabilities

### New Capabilities
- `slide-ir`: the validated, template-agnostic intermediate representation that the LLM emits
  and the compiler consumes — the single source of truth shared by agents, compiler, and frontend.

### Modified Capabilities
<!-- none — greenfield -->

## Non-goals

- The deterministic IR→pptx compiler (separate change `add-pptx-compiler`).
- Agents / LangGraph orchestration (separate change).
- Formula / table rendering or extraction (separate changes).

## Impact

- New package `packages/core/ir/` — the root contract; depends on nothing in the repo.
- New dependency: **`pydantic` v2 (MIT)** — allowed. No AGPL/GPL introduced.
- Produces the JSON Schema artifact later consumed by `apps/web` for TS types.
