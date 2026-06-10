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
The web UI SHALL be a three-view application (generate, visual approval, result) with a sidebar of
past jobs (status, open, delete), a generation view exposing per-job options (style, parser, opt-in
toggles) with staged live progress, a visual approval view presenting real rendered slide images with
approve and reject-with-feedback actions, and a result view with per-slide preview and download. It
SHALL remain export-first (no embedded editor) and degrade to a text outline when no renderer exists.

#### Scenario: Visual approval
- **WHEN** generation reaches the Hard-Stop on a host with a slide renderer
- **THEN** the user reviews rendered slide thumbnails and may approve or reject with feedback

#### Scenario: Renderer-less degradation
- **WHEN** no renderer is available
- **THEN** the approval view falls back to the text outline and approval still works

#### Scenario: Rejection replans live
- **WHEN** the user rejects with feedback
- **THEN** the replan progress streams in the UI and ends at a fresh visual approval

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

### Requirement: Parse-quality feedback
The upload response SHALL include parse warnings, and the web UI SHALL show a warning when a parse
looks thin so the user can react before spending generation.

#### Scenario: A thin parse warns the user
- **WHEN** the upload response carries a parse warning
- **THEN** the UI displays that warning

