# api Specification

## Purpose
TBD - created by archiving change add-api-app. Update Purpose after archive.
## Requirements
### Requirement: Create a job from inputs
`POST /jobs` SHALL ingest the provided input paths into an Evidence Pool and register a job,
returning a `job_id`.

#### Scenario: Job is created with ingested evidence
- **WHEN** `POST /jobs` is called with input file paths
- **THEN** it returns a `job_id` and the inputs are ingested into the job's initial state

### Requirement: Stream planning to the Hard-Stop
`GET /jobs/{job_id}/stream` SHALL stream per-node progress as Server-Sent Events and end with an
`awaiting_approval` event carrying the outline, without compiling a deck.

#### Scenario: Stream yields progress then awaits approval
- **WHEN** the stream endpoint is consumed for a created job
- **THEN** it emits at least one node update and an `awaiting_approval` event containing the outline
- **AND** no `.pptx` has been produced yet

### Requirement: Approve resumes and produces a deck
`POST /jobs/{job_id}/approve` SHALL resume the interrupted run with the approval payload and
produce a native `.pptx`, returning its path.

#### Scenario: Approval completes the run
- **WHEN** `POST /jobs/{job_id}/approve` is called after the stream paused
- **THEN** the run resumes, a `.pptx` is produced, and its `output_path` is returned

### Requirement: Download the produced deck
`GET /jobs/{job_id}/download` SHALL return the produced `.pptx` file.

#### Scenario: Deck is downloadable
- **WHEN** the deck has been produced and `GET /jobs/{job_id}/download` is called
- **THEN** it returns the `.pptx` bytes

### Requirement: Provider-agnostic app
The app SHALL be constructed around an injected `LLM`, so a fake or a real provider can be used.

#### Scenario: App runs with a fake LLM
- **WHEN** the app is created with a `FakeLLM`
- **THEN** the full create -> stream -> approve -> download flow works without any network call

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

### Requirement: Detached, resumable job streams
Job execution SHALL be detached from the SSE connection (a disconnect never aborts generation), the
stream SHALL replay the run's event log on reconnect and emit keepalives when idle, generation
failures SHALL surface as an error event carrying the reason, and the stream endpoint SHALL resume a
stranded job from its last checkpoint.

#### Scenario: Reconnect replays the Hard-Stop
- **WHEN** a client reconnects to a job paused at approval
- **THEN** the stream immediately replays the awaiting_approval event

#### Scenario: Generation failure is surfaced
- **WHEN** planning fails irrecoverably
- **THEN** the stream emits an error event with the message instead of dropping silently

### Requirement: Jobs survive restarts
With the durable checkpointer, a job at the Hard-Stop SHALL remain approvable after a server restart,
and a job killed mid-run SHALL list as interrupted and resume from its last completed node.

#### Scenario: Approve across a restart
- **WHEN** the server restarts while a job awaits approval
- **THEN** approval on the new process compiles and the deck downloads

