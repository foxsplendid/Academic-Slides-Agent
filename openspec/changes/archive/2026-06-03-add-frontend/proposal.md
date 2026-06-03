## Why

The pipeline is curl-only. Non-technical researchers need a UI. This adds a minimal **export-first**
React SPA that drives the whole flow, plus the two API enablers a browser needs: **file upload** and
**CORS**. No in-browser editing (avoids AGPL PPTist; users edit the exported `.pptx` in PowerPoint).

## What Changes

- API additions (in `asa_api`):
  - **`POST /jobs/upload`** — multipart file upload → saved under the workspace → ingested → a job
    (so the browser can submit a paper + supplementary files without server-side paths).
  - **CORS middleware** — allow the frontend origin(s); configurable via `ASA_CORS_ORIGINS`.
- **`apps/web/`** — a Vite + React + TypeScript SPA: upload files → Generate → **stream progress**
  (SSE) → **review the outline tree** (the Hard-Stop) → Approve → **Download `.pptx`**.

## Capabilities

### New Capabilities
- `web-ui`: a browser frontend (and the upload/CORS API enablers) that drives create -> stream ->
  approve -> download for non-technical users.

### Modified Capabilities
<!-- adds upload + CORS to the running app; existing api endpoints are unchanged -->

## Non-goals

- In-browser WYSIWYG slide editing (export-first; edit the `.pptx` in PowerPoint).
- A pixel-accurate slide preview (MVP shows the outline tree for review); auth/multi-user; Next.js SSR.

## Impact

- `asa-api` gains **`python-multipart`** (Apache-2.0) for uploads + CORS middleware (Starlette, BSD).
- New `apps/web/` with React/Vite/TypeScript — all MIT. Verified by `tsc` + `vite build`.
