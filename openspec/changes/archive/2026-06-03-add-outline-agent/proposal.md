## Why

The deterministic core can render Slide-IR, but nothing yet *produces* IR from a paper. This
adds the first agent — provider-agnostic and fully unit-testable — that turns the Evidence Pool
into a Slide-IR `Deck`, with the human Hard-Stop modeled as explicit state transitions. MVP
step 4 (docs/SPEC.md §10). It introduces no LLM SDK and no network, so it ships testable today.

## What Changes

- Add `packages/agents/` (`asa_agents`):
  - **`LLM` Protocol** — `complete(prompt, *, system=None) -> str` — provider-agnostic interface.
  - **`FakeLLM`** — a scripted test/dev double (records calls, returns queued responses).
  - **`build_outline(assets, tables, llm) -> Deck`** — builds an evidence prompt, calls the LLM,
    and parses the result **through the Slide-IR boundary** (`from_llm_output`), so non-IR output
    is rejected and never reaches the compiler.
  - **Hard-Stop workflow** — `plan_outline(state, ...)` pauses at `Phase.AWAIT_OUTLINE_APPROVAL`;
    `approve_outline(state, edits)` advances to `Phase.MAPPING`.

## Capabilities

### New Capabilities
- `outline-agent`: produce a Slide-IR `Deck` from the Evidence Pool via a provider-agnostic LLM,
  enforcing the IR boundary, and gate it behind a human Hard-Stop.

### Modified Capabilities
<!-- consumes slide-ir (Deck, GenerationState, from_llm_output); no spec change there -->

## Non-goals

- Real LLM provider adapters (OpenAI/Anthropic/…) and key management — a later change.
- LangGraph wiring, streaming, checkpoint/resume — a later change (`add-langgraph-orchestration`).
- The Critic loop and multi-agent decomposition — later.

## Impact

- New package `packages/agents/`; depends only on **`asa-slide-ir`** (no LLM SDK, no network).
- Establishes the seam (`LLM` Protocol) that real providers and LangGraph will plug into next.
