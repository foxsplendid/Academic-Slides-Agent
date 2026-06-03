## ADDED Requirements

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
