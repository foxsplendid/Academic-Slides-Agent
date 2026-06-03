## ADDED Requirements

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
