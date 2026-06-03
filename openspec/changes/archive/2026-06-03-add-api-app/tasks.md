## 1. Package setup

- [x] 1.1 Create `apps/api/` package (`pyproject.toml`, `asa_api/`)
- [x] 1.2 Deps: `fastapi` (MIT) + local `asa-agents`/`asa-ingestion`/`asa-slide-ir`; dev `httpx`, `pytest`

## 2. App factory

- [x] 2.1 `create_app(llm, *, formula_renderer=None, out_dir="exports") -> FastAPI` — build graph once; in-memory job registry
- [x] 2.2 `_cfg(job_id)` thread config; small accessor for snapshot/return field (dict or model)

## 3. Endpoints

- [x] 3.1 `POST /jobs` — ingest `inputs` → initial `GenerationState` → `{job_id}`
- [x] 3.2 `GET /jobs/{job_id}/stream` — SSE node updates; end with `awaiting_approval` (outline); no compile
- [x] 3.3 `POST /jobs/{job_id}/approve` — `Command(resume=...)` → compile → `{output_path}`
- [x] 3.4 `GET /jobs/{job_id}/download` — `FileResponse` of the `.pptx`

## 4. Tests (TestClient + FakeLLM)

- [x] 4.1 `POST /jobs` returns a job_id (ingesting a CSV input)
- [x] 4.2 Stream emits a node update + `awaiting_approval` with outline; no `.pptx` yet
- [x] 4.3 `approve` resumes and returns an existing `output_path`
- [x] 4.4 `download` returns pptx bytes (zip signature `PK`)
- [x] 4.5 Full create -> stream -> approve -> download works with `FakeLLM` (no network)
