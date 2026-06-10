## ADDED Requirements

### Requirement: Staged quality loop in the critic node
The critic node SHALL run quality stages cheapest-first — IR checks, then the geometry lint on a
throwaway compile, then the opt-in visual critique — and SHALL feed any stage's findings into the
existing bounded repair loop.

#### Scenario: Lint findings trigger a repair pass
- **WHEN** the IR checks pass but the geometry lint reports a crammed slide
- **THEN** the graph routes back to the planner with that finding
