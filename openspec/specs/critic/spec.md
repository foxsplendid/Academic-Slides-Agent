# critic Specification

## Purpose
TBD - created by archiving change add-critic-loop. Update Purpose after archive.
## Requirements
### Requirement: Deterministic deck critic
The system SHALL provide an AI-free `critique_deck(slides, evidence)` that measures Slide-IR and
returns a list of human-readable findings, flagging empty content slides, empty or over-long titles,
over-long bullet lists, over-large tables, layout/block mismatches, and figure blocks whose
`asset_id` is absent from the Evidence Pool. A `two_column_table` layout SHALL be considered satisfied
by a `table`, `chart`, **or** `diagram` block.

#### Scenario: A chart satisfies the two_column_table layout
- **WHEN** a slide uses the `two_column_table` layout with a `chart` (or `diagram`) block and no table
- **THEN** the critic does NOT flag a missing-table mismatch for that slide

### Requirement: Bounded critic retry loop
The orchestration graph SHALL run the critic before the human Hard-Stop and, when findings exist and
the retry budget is not exhausted, re-plan with those findings as feedback; otherwise it SHALL
proceed to approval. The number of re-plans SHALL be bounded by `max_retries`.

#### Scenario: Self-correction before approval
- **WHEN** the planner first emits a deck with a defect and then, given the critic's feedback, emits a
  clean deck
- **THEN** the graph re-plans once and reaches the approval Hard-Stop with no findings

#### Scenario: Budget exhaustion still reaches the human
- **WHEN** the planner keeps emitting a defective deck across every retry
- **THEN** the loop stops after `max_retries` re-plans and still reaches the approval Hard-Stop with
  the residual findings recorded in state

### Requirement: Diagram edge validation
The critic SHALL flag a diagram edge whose `source` or `target` does not match a defined node id.

#### Scenario: A dangling edge is flagged
- **WHEN** a diagram has an edge referencing a node id not present in its nodes
- **THEN** the critic reports the dangling edge

### Requirement: Redundancy and layout findings
The critic SHALL flag a `title`/`section` divider that carries content blocks as a repair-routable
finding (naming the slide for in-place relayout), and SHALL flag near-duplicate content-slide titles as
a non-repair-routable finding (so the human, not the in-place repair loop, resolves the redundancy).

#### Scenario: Divider with content is repair-routable
- **WHEN** a `section` slide carries a bullet block
- **THEN** the finding names the slide so the repair loop can relayout it

#### Scenario: Duplicate-title finding is human-facing
- **WHEN** two content slides have near-duplicate titles
- **THEN** the finding names both slides but is not phrased to trigger the in-place repair loop

### Requirement: Figure-led layout consistency
The critic SHALL flag any figure-led layout (`figure_caption`, `figure_left`, `big_figure`,
`figure_grid`) that carries no figure block, naming the slide for repair.

#### Scenario: figure_left without a figure is flagged
- **WHEN** a `figure_left` slide has no figure block
- **THEN** a repair-routable finding names that slide

### Requirement: Render-grounded quality checks
The quality loop SHALL include a deterministic post-compile geometry lint (text at the auto-shrink
floor, figure-led slides with tiny figures, overlapping content shapes) whose findings name the slide
for repair, and MAY include an opt-in VLM visual critique restricted to a closed defect taxonomy that
emits IR-level suggestions. Both stages SHALL fail open (a check failure never blocks generation).

#### Scenario: Crammed text is flagged for repair
- **WHEN** a compiled slide's body text sits at the auto-shrink floor
- **THEN** a finding names that slide and suggests shortening or splitting

#### Scenario: VLM critique is taxonomy-bound
- **WHEN** the vision model reports a defect outside the closed taxonomy
- **THEN** it is discarded

### Requirement: Layout monotony detection
The critic SHALL flag more than three consecutive content slides sharing one layout as a
repair-routable finding naming a slide inside the run; structural dividers and the TOC reset the run.

#### Scenario: A five-slide run is flagged
- **WHEN** five consecutive content slides share `bullet_evidence`
- **THEN** a finding names a slide in the run and suggests varying the composition

