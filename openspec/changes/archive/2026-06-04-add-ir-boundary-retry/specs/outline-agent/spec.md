## ADDED Requirements

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
