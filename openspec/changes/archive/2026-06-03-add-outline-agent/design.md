## Context

The compiler/formula/ingestion layers are deterministic and done. This change adds the first
*generative* step — but keeps it provider-agnostic and unit-testable so it ships now and does not
lock in an LLM vendor. The real providers and LangGraph orchestration are deliberately deferred.

## Goals / Non-Goals

**Goals:**
- A minimal `LLM` Protocol + a `FakeLLM` test double.
- `build_outline(assets, tables, llm) -> Deck` that enforces the Slide-IR boundary.
- Hard-Stop modeled as explicit `GenerationState` transitions, testable without LangGraph.

**Non-Goals:**
- Real provider adapters / key management; LangGraph; streaming; Critic; multi-agent.

## Decisions

- **Provider-agnostic `LLM` Protocol (`complete`)** — the agent never imports a vendor SDK; real
  adapters implement the Protocol later. `FakeLLM` enables deterministic unit tests with no network.
- **Reuse `from_llm_output` as the boundary** — the agent's only accepted output is validated
  Slide-IR; prose/code/HTML are rejected here (the "LLM locked to IR" invariant, SPEC §3.1).
- **Hard-Stop as state transitions, not LangGraph yet** — `plan_outline` sets
  `AWAIT_OUTLINE_APPROVAL`; `approve_outline` advances to `MAPPING`. LangGraph `interrupt()` will
  wrap these in the next change; modeling them as pure functions keeps them testable now.
- **Sync `complete` for the scaffold** — simplest to test; async/streaming arrives with LangGraph.
- **Evidence digest is truncated** — a compact, provenance-tagged summary keeps the prompt bounded.

## Risks / Trade-offs

- [Outline *quality* depends on prompt + a real LLM, untestable here] → this change proves the
  *plumbing* (boundary, Hard-Stop, evidence flow); prompt tuning happens with a real provider later.
- [Sync interface may need async later] → contained behind the `LLM` Protocol; adapters can offer
  both, and LangGraph nodes can wrap sync calls.
