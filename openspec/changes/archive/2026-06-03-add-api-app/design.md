## Context

The graph (orchestration) is a compiled LangGraph with `interrupt()` + checkpointer + streaming.
This change gives it an HTTP surface for a self-hosted deployment and a future frontend. It stays
provider-agnostic (the `LLM` is injected) and fully TestClient-testable.

## Goals / Non-Goals

**Goals:**
- `create_app(llm, ...)` factory; endpoints for create / stream(SSE) / approve(resume) / download.
- The Hard-Stop is surfaced over SSE; approval resumes the same checkpointed run.

**Non-Goals:**
- Uploads/auth/multi-user; real provider; durable persistence; WebSocket; resume-phase streaming.

## Decisions

- **App factory + injected `LLM`** — no global model; tests pass `FakeLLM`. The graph is built once
  per app; the checkpointer (MemorySaver) holds each run's state under `thread_id = job_id`.
- **SSE, not WebSocket** — simplest streaming that works with `StreamingResponse` and is buffered by
  TestClient for assertions. WebSocket can be added later.
- **Stream endpoint runs the planning phase**; it ends at the interrupt and emits `awaiting_approval`
  (read from `graph.get_state`). `approve` resumes via `Command(resume=...)` (sync; compile is one node).
- **Progress events are compact** (node name + phase), since slides carry non-JSON objects; the
  outline (list of dicts) is JSON-safe and sent in `awaiting_approval`.
- **Inputs are file paths** for the MVP (self-hosted tool); real uploads are a later change.

## Risks / Trade-offs

- [In-memory registry + MemorySaver are per-process] → fine for self-hosted single-instance MVP;
  durable stores come later.
- [Reading LangGraph snapshot/return shapes (dict vs model)] → handled with a small field accessor
  that works for both; covered by runnable TestClient tests.
- [Sync graph calls inside async endpoints] → FastAPI runs sync endpoints in a threadpool; acceptable
  for MVP throughput.
