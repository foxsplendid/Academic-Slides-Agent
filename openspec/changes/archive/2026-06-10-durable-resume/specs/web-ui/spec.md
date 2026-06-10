## ADDED Requirements

### Requirement: Reconnect and resume UX
The web UI SHALL tolerate transient stream drops (auto-reconnect against the replayable log, with a
clear message that the job continues server-side after repeated failures) and SHALL let the user open
running, interrupted, or awaiting-approval jobs from the history to attach, resume, or approve.

#### Scenario: Interrupted job is resumable from history
- **WHEN** the user clicks a job listed as interrupted
- **THEN** the UI attaches to a resumed run and shows its live progress
