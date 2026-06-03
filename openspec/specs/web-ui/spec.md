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

