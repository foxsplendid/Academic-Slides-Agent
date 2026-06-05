# web-ui Specification

## Purpose
TBD - created by archiving change add-frontend. Update Purpose after archive.
## Requirements
### Requirement: Browser file upload creates a job
`POST /jobs/upload` SHALL accept multipart file uploads, ingest them into an Evidence Pool, and
register a job, returning a `job_id`.

#### Scenario: Uploaded files create a job
- **WHEN** a CSV is uploaded to `POST /jobs/upload`
- **THEN** a `job_id` is returned and the uploaded file is ingested into the job's initial state

### Requirement: CORS allows the frontend origin
The app SHALL emit CORS headers permitting configured origins so a browser SPA can call it.

#### Scenario: Allowed origin receives CORS headers
- **WHEN** a request includes an allowed `Origin`
- **THEN** the response carries an `access-control-allow-origin` header for that origin

### Requirement: End-to-end via upload
The full flow starting from an upload (upload -> stream -> approve -> download) SHALL produce a
downloadable `.pptx`.

#### Scenario: Upload-driven flow yields a deck
- **WHEN** a job is created via upload and then streamed, approved, and downloaded
- **THEN** the downloaded response is a `.pptx`

### Requirement: Browser frontend drives the flow
A built web SPA SHALL target the API endpoints to upload inputs, stream progress, review the
outline, approve, and download — without an in-browser editor.

#### Scenario: SPA builds and targets the endpoints
- **WHEN** the frontend is built
- **THEN** the build succeeds and the bundle references the create/stream/approve/download endpoints

### Requirement: Live progress panel
The web UI SHALL display generation progress as distinct phases and, during slide generation, a live
slide counter, driven by `progress` SSE events.

#### Scenario: Slide progress is shown
- **WHEN** the stream emits `progress` events with `done`/`total` during slide generation
- **THEN** the UI shows the current phase and the slide counter (e.g. "3 / 10")

### Requirement: Supplementary-aware upload feedback
The upload response SHALL report per-type ingestion counts, and the web UI SHALL present a
supplementary-aware file picker and show those counts after upload.

#### Scenario: Upload reports what was ingested
- **WHEN** files are uploaded
- **THEN** the response includes counts of ingested files, tables, and figures

