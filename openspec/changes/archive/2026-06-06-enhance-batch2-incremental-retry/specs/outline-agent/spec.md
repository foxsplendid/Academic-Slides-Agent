## ADDED Requirements

### Requirement: Incremental critic repair
On a critic retry the two-stage builder SHALL, given the prior slides and the findings, re-generate
only the flagged slides (a focused repair pass) and keep the unflagged slides unchanged, rather than
re-running the whole skeleton-and-expand pipeline.

#### Scenario: Only the flagged slide is re-generated
- **WHEN** the builder is given prior slides plus feedback naming one slide id
- **THEN** it makes a repair call only for that slide and returns the other slides unchanged
