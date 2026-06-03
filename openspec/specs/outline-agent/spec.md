# outline-agent Specification

## Purpose
TBD - created by archiving change add-outline-agent. Update Purpose after archive.
## Requirements
### Requirement: Agent output passes the Slide-IR boundary
The outline agent SHALL parse the LLM's output through the Slide-IR boundary, returning a valid
`Deck` for valid IR and raising for anything that is not valid Slide-IR.

#### Scenario: Valid IR is returned as a Deck
- **WHEN** the LLM returns a valid Slide-IR Deck JSON
- **THEN** `build_outline` returns a `Deck` with those slides

#### Scenario: Non-IR output is rejected
- **WHEN** the LLM returns prose or non-IR text
- **THEN** `build_outline` raises an IR boundary error and produces no deck

### Requirement: Provider-agnostic LLM interface
The agent SHALL depend only on an `LLM` interface exposing `complete(prompt, *, system=None) -> str`,
so any provider (or a fake) can be supplied.

#### Scenario: Any LLM implementation is usable
- **WHEN** a `FakeLLM` is supplied to `build_outline`
- **THEN** the agent calls its `complete` and uses the returned text

### Requirement: Evidence is given to the LLM
The agent SHALL include the Evidence Pool content (text and table summaries) in the prompt and a
system instruction describing the academic structure and IR-only output rule.

#### Scenario: Prompt carries evidence and system instruction
- **WHEN** `build_outline` is called with evidence
- **THEN** the LLM receives a prompt containing that evidence and a non-empty system instruction

### Requirement: Human Hard-Stop before rendering
Planning the outline SHALL pause the workflow at `AWAIT_OUTLINE_APPROVAL` (the Hard-Stop) without
proceeding to rendering.

#### Scenario: Planning pauses for approval
- **WHEN** `plan_outline` runs successfully
- **THEN** the state's phase is `AWAIT_OUTLINE_APPROVAL`, its slides are populated, and it is not yet approved

### Requirement: Approval advances the workflow
Approving the outline SHALL mark it approved (capturing any edits) and advance past the Hard-Stop.

#### Scenario: Approval advances to mapping
- **WHEN** `approve_outline` is called with optional edits
- **THEN** the state is marked approved, edits are recorded, and the phase advances to `MAPPING`

### Requirement: 组会 narrative with speaker notes
The planner SHALL produce a Chinese research-group-meeting talk following a method-paper narrative
(science question → background → data/method → results/validation → discussion → innovation/outlook),
with concise one-line slide titles, a per-slide interpretation, and oral speaker notes, while keeping
technical terms, symbols, method names, and citations in their original form.

#### Scenario: A generated deck carries notes and concise titles
- **WHEN** the planner builds a deck from evidence
- **THEN** content slides carry non-empty `speaker_notes` and titles within the length budget

### Requirement: Figures are grounded in the Evidence Pool
The planner SHALL be told which figure asset_ids exist and SHALL emit a `figure` block only for an
asset_id in that set; a figure that is not available SHALL be described as text instead.

#### Scenario: No figures available yields no figure blocks
- **WHEN** the Evidence Pool contains no figure assets
- **THEN** the generated deck contains no `figure` blocks (and the critic reports no dangling figure
  references)

