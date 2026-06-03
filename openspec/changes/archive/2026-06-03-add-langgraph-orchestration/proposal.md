## Why

The pipeline's pieces exist (ingestion, outline agent, compiler, formula) but are not wired with
real human-in-the-loop, persistence, or streaming. This wires them into a **LangGraph** graph that
delivers the three headline requirements (docs/SPEC.md §5): `interrupt()` for the Hard-Stop,
checkpointer for resume, streaming for progress. MVP step 5 — still FakeLLM-testable, no provider.

## What Changes

- Add `asa_agents/graph.py` — `build_graph(llm, *, formula_renderer=None, out_dir="exports", checkpointer=None)`
  returning a compiled `StateGraph(GenerationState)` with nodes:
  - `plan` — runs the outline agent (LLM → IR boundary), sets slides/outline, phase `AWAIT_OUTLINE_APPROVAL`.
  - `approval` — calls `interrupt({"outline": ...})` (the **Hard-Stop**); on resume applies approval/edits, phase `MAPPING`.
  - `compile` — renders the deck to a native `.pptx`, sets `output_path`, phase `DONE`.
  - Compiled with a checkpointer (`MemorySaver` default) → resumable across the interrupt.
- Extend `GenerationState` (additive): `tables: list[TableBlock]` and `output_path: Optional[str]`
  — the workflow state must carry the ingested tables and the produced deck path.
- Add deps to `asa-agents`: **`langgraph` (Apache-2.0)** + `asa-pptx-compiler` (local).

## Capabilities

### New Capabilities
- `orchestration`: a LangGraph state machine that runs outline → Hard-Stop → compile, with
  interrupt-based human approval, checkpoint/resume, and per-node streaming.

### Modified Capabilities
<!-- GenerationState gains two additive fields; no existing slide-ir requirement constrains its field set -->

## Non-goals

- Real LLM provider adapters (still injected as the `LLM` Protocol; FakeLLM in tests).
- The Critic retry loop, multi-agent decomposition — later.
- Durable checkpointing (Sqlite/Postgres) and the streaming **frontend** — `MemorySaver` here, pluggable.

## Impact

- `asa-agents` now imports **`langgraph`** (per SPEC §5, only `packages/agents/` may) + the compiler.
- New transitive deps (langchain-core MIT, etc.) — all permissive; no AGPL/GPL.
- `GenerationState` gains `tables` / `output_path` (additive, backward-compatible).
