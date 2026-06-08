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

### Requirement: Resilient IR boundary
The planner SHALL retry a malformed LLM response at the IR boundary up to a bounded number of attempts,
feeding the validation error back so the model can correct it, and SHALL re-raise `IRBoundaryError`
only after the budget is exhausted. A valid response SHALL be accepted on the first attempt without
extra calls.

#### Scenario: A transient malformed response is recovered
- **WHEN** the LLM first returns invalid Slide-IR and then, on re-ask, returns a valid deck
- **THEN** `build_outline` returns the valid deck

#### Scenario: A persistently non-IR model still aborts
- **WHEN** the LLM never returns valid Slide-IR within the attempt budget
- **THEN** `build_outline` raises `IRBoundaryError`

### Requirement: Two-stage detailed deck
The planner SHALL offer a two-stage builder that first produces a slide skeleton (per slide: title,
layout, a focus, the evidence pages it draws on, and an optional figure) and then expands each slide
with a focused call given that slide's evidence at full resolution, yielding deeper per-slide content
(substantive bullets, an interpretation, and speaker notes) than the single-shot builder. The
assembled deck SHALL pass the strict IR boundary.

#### Scenario: Per-slide expansion deepens content
- **WHEN** the two-stage builder runs against evidence with the LLM scripted to return a skeleton and
  then a detailed slide per plan
- **THEN** it returns a valid `Deck` whose slides carry the expanded bullets and non-empty speaker notes

#### Scenario: A figure slide keeps its assigned figure
- **WHEN** the skeleton assigns a `figure_id` to a slide and that id exists in the Evidence Pool
- **THEN** the expanded slide contains a `figure` block with that `asset_id`

### Requirement: Parallel slide expansion with serial fallback
The two-stage builder SHALL expand slides concurrently by default and SHALL fall back to serial
expansion if the parallel path raises, always returning slides in skeleton order.

#### Scenario: Parallel expansion preserves order
- **WHEN** the detailed builder expands a multi-slide skeleton in parallel
- **THEN** the returned deck's slides are in the skeleton's order

#### Scenario: Failure falls back to serial
- **WHEN** a parallel worker raises during expansion
- **THEN** the builder retries serially and still returns a valid deck

### Requirement: Progress reporting
The two-stage builder SHALL accept a progress callback and invoke it for the skeleton stage and for
each expanded slide with a done/total count.

#### Scenario: Progress callback receives slide counts
- **WHEN** the builder runs with a progress callback
- **THEN** the callback is invoked with slide `done` and `total` values

### Requirement: Charts only from evidence data
The planner MAY emit a `ChartBlock` to visualize quantitative results, but its values SHALL come from
data present in the evidence; the planner SHALL NOT fabricate chart numbers.

#### Scenario: Prompt forbids fabricated chart data
- **WHEN** the planner prompts are produced
- **THEN** they instruct that chart values must come from the evidence and must not be invented

### Requirement: Supplementary data reaches per-slide expansion
The two-stage builder SHALL let a slide reference ingested data tables (`table_refs`) and SHALL inject
those tables' actual data (header + rows, capped with a remainder note) into the slide's expansion
prompt, so a slide can build a chart or discussion from supplementary data.

#### Scenario: A referenced table's data is given to expansion
- **WHEN** a slide plan lists a `table_refs` index and the builder expands that slide
- **THEN** the expansion prompt contains that table's column headers and data rows

### Requirement: Diagrams from the paper's logic
The planner SHALL emit a `DiagramBlock` only with nodes/edges that reflect a structure present in the
evidence and SHALL NOT fabricate relationships (it may visualize a process, comparison, or
relationship the paper actually describes).

#### Scenario: Prompt forbids fabricated relationships
- **WHEN** the planner prompts are produced
- **THEN** they instruct that diagram nodes/edges must come from the paper and must not be invented

### Requirement: Mandatory interpretation line
The two-stage expand prompt SHALL require each content slide's final bullet to be an interpretation
line beginning with "→ " (what the slide means), so the "so-what" is consistently present.

#### Scenario: Prompt requires the interpretation line
- **WHEN** the expand prompt is produced
- **THEN** it states that the last bullet must begin with "→ " and is not optional

### Requirement: Incremental critic repair
On a critic retry the two-stage builder SHALL, given the prior slides and the findings, re-generate
only the flagged slides (a focused repair pass) and keep the unflagged slides unchanged, rather than
re-running the whole skeleton-and-expand pipeline.

#### Scenario: Only the flagged slide is re-generated
- **WHEN** the builder is given prior slides plus feedback naming one slide id
- **THEN** it makes a repair call only for that slide and returns the other slides unchanged

### Requirement: Tunable, measurable, depth-safe expansion latency
The detailed builder SHALL read expansion concurrency from `ASA_EXPAND_WORKERS` (default 6), SHALL cap
per-slide evidence adaptively (full context for figure/table slides, tighter for plain bullet slides),
and SHALL constrain output length (concise speaker notes and bullets) without reducing the substantive
bullet count. When `ASA_DEBUG_TIMING` is set it SHALL emit a timing event reporting wall time versus the
sum of per-call times.

#### Scenario: Concurrency is tunable via env
- **WHEN** `ASA_EXPAND_WORKERS=2` and a multi-slide deck is expanded
- **THEN** at most two slide expansions are in flight at once

#### Scenario: Evidence is capped adaptively
- **WHEN** a plain bullet slide and a figure slide reference an over-long page
- **THEN** the plain slide's prompt carries less evidence than the figure slide's

