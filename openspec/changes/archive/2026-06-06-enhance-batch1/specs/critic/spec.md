## MODIFIED Requirements

### Requirement: Deterministic deck critic
The system SHALL provide an AI-free `critique_deck(slides, evidence)` that measures Slide-IR and
returns a list of human-readable findings, flagging empty content slides, empty or over-long titles,
over-long bullet lists, over-large tables, layout/block mismatches, and figure blocks whose
`asset_id` is absent from the Evidence Pool. A `two_column_table` layout SHALL be considered satisfied
by a `table`, `chart`, **or** `diagram` block.

#### Scenario: A chart satisfies the two_column_table layout
- **WHEN** a slide uses the `two_column_table` layout with a `chart` (or `diagram`) block and no table
- **THEN** the critic does NOT flag a missing-table mismatch for that slide
