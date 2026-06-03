## Why

The orchestration graph is library-only. To be usable (and to drive a frontend), it needs an
HTTP surface with **streaming** progress and a **Hard-Stop resume** endpoint — self-hosted for
privacy. This wraps the graph in FastAPI, provider-agnostic and FakeLLM-testable.

## What Changes

- Add `apps/api/` (`asa_api`) with `create_app(llm, *, formula_renderer=None, out_dir="exports") -> FastAPI`
  that builds the graph once (checkpointer keyed by `job_id`) and exposes:
  - `POST /jobs` — ingest `inputs` (file paths) → initial `GenerationState`; returns `{job_id}`.
  - `GET /jobs/{job_id}/stream` — **SSE**: per-node progress updates, ending with an
    `awaiting_approval` event carrying the outline (the Hard-Stop).
  - `POST /jobs/{job_id}/approve` — **resume** the interrupt with approval/edits → compile → `{output_path}`.
  - `GET /jobs/{job_id}/download` — the produced `.pptx`.
- In-memory job registry; the LangGraph checkpointer holds the run state per `job_id`.

## Capabilities

### New Capabilities
- `api`: a FastAPI service exposing job creation, SSE streaming to the Hard-Stop, resume-on-approval,
  and deck download — provider-agnostic.

### Modified Capabilities
<!-- consumes orchestration + ingestion; no spec change there -->

## Non-goals

- Real file uploads (MVP takes local paths — it is a self-hosted tool), auth, multi-user.
- Real LLM provider wiring (the `LLM` is injected; FakeLLM in tests).
- Durable persistence (MemorySaver), WebSocket (SSE only), streaming the resume/compile phase.

## Impact

- New app package `apps/api/`. New dependency **`fastapi`** (MIT); dev **`httpx`** (BSD) for TestClient.
- Depends on `asa-agents` (graph), `asa-ingestion`, `asa-slide-ir` — all local, permissive.
