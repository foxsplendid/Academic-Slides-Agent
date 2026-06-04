## ADDED Requirements

### Requirement: Injectable planner
The graph SHALL accept an injectable planner callable (default: the single-shot `build_outline`) so a
detailed multi-stage planner can drive production runs without changing the graph's structure.

#### Scenario: Default planner is unchanged
- **WHEN** a graph is built without specifying a planner
- **THEN** it plans with the single-shot builder and reaches the approval Hard-Stop as before

#### Scenario: A custom planner is used
- **WHEN** a graph is built with a custom planner callable
- **THEN** the plan node uses that callable to produce the deck
