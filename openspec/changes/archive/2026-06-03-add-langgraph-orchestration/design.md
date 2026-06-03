## Context

All pipeline stages exist as pure/testable units. This change composes them with LangGraph to get
the SPEC §5 trio — `interrupt()` (Hard-Stop), checkpointer (resume), streaming — without bespoke
session plumbing. Per SPEC §5, only `packages/agents/` imports LangGraph.

## Goals / Non-Goals

**Goals:**
- A compiled `StateGraph(GenerationState)`: `plan → approval(interrupt) → compile`.
- Resumable across the Hard-Stop; streamable; FakeLLM-testable.

**Non-Goals:**
- Real providers; Critic loop; durable checkpoints; streaming frontend.

## Decisions

- **Interrupt lives in a separate `approval` node, not in `plan`.** On resume, LangGraph re-runs
  only the interrupted node — keeping the LLM call (in `plan`) from firing twice. This is the key
  correctness reason to split planning from the approval gate.
- **`GenerationState` is the graph state**, extended additively with `tables` + `output_path`. It is
  literally "the LangGraph state" (its docstring), so it should carry the working data and result.
- **Dependencies injected via a `build_graph(...)` closure** (`llm`, `formula_renderer`, `out_dir`) —
  nodes stay pure-ish; no globals; tests pass a `FakeLLM`.
- **`MemorySaver` default checkpointer, pluggable.** Durable Sqlite/Postgres is a later concern; the
  resume *mechanism* is proven with MemorySaver.
- **IR boundary stays in `plan`** (via `build_outline` → `from_llm_output`) so bad output aborts
  before any rendering.

## Risks / Trade-offs

- [LangGraph API churn] → pinned import surface (`StateGraph`, `interrupt`, `Command`, `MemorySaver`)
  verified against the installed version; covered by runnable tests.
- [Re-running the approval node on resume] → intentional and cheap (it only applies the decision); the
  expensive LLM work is isolated in `plan`.
- [Pydantic state + checkpoint serialization] → MemorySaver keeps objects in-process; durable savers
  will need the state to be serializable (Slide-IR already is JSON-friendly).
