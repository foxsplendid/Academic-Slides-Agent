## ADDED Requirements

### Requirement: Live progress panel
The web UI SHALL display generation progress as distinct phases and, during slide generation, a live
slide counter, driven by `progress` SSE events.

#### Scenario: Slide progress is shown
- **WHEN** the stream emits `progress` events with `done`/`total` during slide generation
- **THEN** the UI shows the current phase and the slide counter (e.g. "3 / 10")
