## ADDED Requirements

### Requirement: Durable checkpointer
The orchestration package SHALL provide a SQLite-backed checkpointer using the project's slide-ir
serializer so graph state survives process restarts.

#### Scenario: State persists across processes
- **WHEN** a new graph instance opens the same checkpoint database
- **THEN** the prior thread's state and pending interrupt are visible
