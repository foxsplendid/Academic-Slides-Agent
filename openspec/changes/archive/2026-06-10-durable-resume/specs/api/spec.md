## ADDED Requirements

### Requirement: Detached, resumable job streams
Job execution SHALL be detached from the SSE connection (a disconnect never aborts generation), the
stream SHALL replay the run's event log on reconnect and emit keepalives when idle, generation
failures SHALL surface as an error event carrying the reason, and the stream endpoint SHALL resume a
stranded job from its last checkpoint.

#### Scenario: Reconnect replays the Hard-Stop
- **WHEN** a client reconnects to a job paused at approval
- **THEN** the stream immediately replays the awaiting_approval event

#### Scenario: Generation failure is surfaced
- **WHEN** planning fails irrecoverably
- **THEN** the stream emits an error event with the message instead of dropping silently

### Requirement: Jobs survive restarts
With the durable checkpointer, a job at the Hard-Stop SHALL remain approvable after a server restart,
and a job killed mid-run SHALL list as interrupted and resume from its last completed node.

#### Scenario: Approve across a restart
- **WHEN** the server restarts while a job awaits approval
- **THEN** approval on the new process compiles and the deck downloads
