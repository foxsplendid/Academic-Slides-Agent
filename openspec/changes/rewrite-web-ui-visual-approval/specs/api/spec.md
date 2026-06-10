## ADDED Requirements

### Requirement: Job history, per-job options, and slide previews
The API SHALL accept per-job generation options on upload (style, parser, figure splitting, visual
critique, native formulas), SHALL list and delete jobs (metadata persisted on disk), SHALL render the
job's current deck to per-slide images on request (the final deck when compiled, else a draft of the
in-flight slides), and SHALL serve the download from disk when in-memory state is gone.

#### Scenario: History lists an uploaded job
- **WHEN** a job is created via upload with a style
- **THEN** `GET /jobs` includes it with that style and a status

#### Scenario: Preview fails open without a renderer
- **WHEN** no slide renderer is available on the host
- **THEN** the preview endpoint returns 503 and generation is unaffected

### Requirement: Rejection resumes over the stream
A pending approval SHALL be rejectable with feedback by re-opening the SSE stream, which resumes the
graph, streams the replan progress, and ends at a new approval Hard-Stop.

#### Scenario: Reject replans to a new Hard-Stop
- **WHEN** the stream is opened with a rejection and feedback
- **THEN** the events end with a new `awaiting_approval` carrying the revised outline
