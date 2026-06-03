## Context

The API exposes create/stream/approve/download but assumes server-side paths and same-origin. A
browser needs uploads + CORS. The frontend stays export-first per docs/SPEC.md §7.

## Goals / Non-Goals

**Goals:**
- A minimal Vite + React + TS SPA driving the full flow via `fetch` + `EventSource` (SSE).
- API: multipart upload endpoint + configurable CORS.

**Non-Goals:**
- In-browser editing; pixel-accurate preview; auth; Next.js/SSR.

## Decisions

- **Vite + React + TS SPA (not Next.js)** — a static self-hosted bundle; no SSR needed. All MIT.
- **`EventSource` for SSE** — native browser streaming for `GET /jobs/{id}/stream`; the app shows a
  progress log and renders the outline tree on the `awaiting_approval` event.
- **Upload endpoint saves to the workspace then ingests** — reuses the existing ingestion; a browser
  cannot pass server paths, so it uploads bytes.
- **CORS via Starlette middleware**, origins from `ASA_CORS_ORIGINS` (default localhost dev ports).
- **Outline-review-only preview for MVP** — the Hard-Stop UI shows the tree; a visual slide preview
  is a later enhancement. Editing happens in PowerPoint after download.

## Risks / Trade-offs

- [Upload temp-file lifecycle] → files land under `out_dir/uploads/<job_id>`; cleanup is a later
  concern (self-hosted MVP).
- [Frontend not unit-tested at runtime] → verified by `tsc` + `vite build`; API additions covered by
  TestClient. Live E2E (Playwright) is a later addition.
- [CORS too permissive if misconfigured] → defaults to localhost only; production sets explicit origins.
