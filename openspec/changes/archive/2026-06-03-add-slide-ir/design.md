## Context

Slide-IR is the keystone contract (see `docs/SPEC.md` §3.1, §4). It must be validatable,
reproducible, template-agnostic, and safe to hand to a deterministic compiler. This change
defines the **data layer only**; compiler, agents, and rendering are out of scope.

## Goals / Non-Goals

**Goals:**
- A precise, validated Pydantic v2 model set: `SlideIR`, the block union, `EvidenceAsset`, `GenerationState`.
- Closed vocabularies (layout types, block types) enforced at parse time.
- JSON Schema export for cross-language (TypeScript) type generation.
- Zero AI and zero rendering dependencies in this layer.

**Non-Goals:**
- Rendering IR to `.pptx`; extracting tables/figures; orchestration.

## Decisions

- **Pydantic v2 (MIT)** for models — fast, native discriminated unions, built-in JSON Schema.
  Alternative considered: dataclasses + `jsonschema` (more manual, weaker validation) → rejected.
- **Discriminated union on `type`** for blocks — type-safe parsing + a clear extension point.
- **`layout_type` as `Enum`/`Literal`** — closed vocabulary; constraining LLM generation = reliability.
- **Framework-agnostic `core`** — no LangChain/LangGraph import here, so orchestration can be
  swapped without touching the contract (SPEC invariant).
- **JSON Schema is the frontend contract** — TS types are generated from it; IR stays the single
  source of truth.

## Risks / Trade-offs

- [Vocabulary too rigid for some papers] → start small; extend `layout_type` via future spec
  changes, never ad-hoc in code.
- [Pydantic→TS generator drift] → pin the generator and add a CI check that TS types match the
  exported schema.
- [Over-modeling early] → keep blocks minimal (formula/table/bullets/figure); add types only when
  a real layout needs one.
