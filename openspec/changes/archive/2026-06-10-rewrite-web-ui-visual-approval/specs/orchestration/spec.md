## ADDED Requirements

### Requirement: Human rejection loop and per-job configuration
The approval node SHALL honor a rejection: the human's feedback becomes findings and the graph
returns to planning, then to a fresh approval. Per-job style and option toggles SHALL be read from
the generation state, overriding server defaults.

#### Scenario: Rejected outline is replanned
- **WHEN** the human rejects with feedback at the Hard-Stop
- **THEN** the planner re-runs with that feedback and a new approval interrupt is raised
