## 1. API enablers

- [x] 1.1 `POST /jobs/upload` — multipart files saved under `out_dir/uploads/<job_id>` then ingested
- [x] 1.2 CORS middleware in `create_app` (origins from `ASA_CORS_ORIGINS`, default localhost dev ports)
- [x] 1.3 Add `python-multipart` to `asa-api`; record in `NOTICE`

## 2. Frontend scaffold

- [x] 2.1 `apps/web/` — `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`
- [x] 2.2 `src/api.ts` — base URL from `VITE_API_BASE`; upload/stream(EventSource)/approve/download helpers

## 3. UI

- [x] 3.1 `src/App.tsx` — state machine: pick files -> Generate -> stream progress -> review outline -> Approve -> Download
- [x] 3.2 Minimal styling; `src/main.tsx` entry

## 4. Tests & build

- [x] 4.1 API: upload creates a job; CORS header present; upload-driven end-to-end yields a `.pptx` (TestClient)
- [x] 4.2 Frontend builds: `tsc --noEmit` + `vite build` succeed
