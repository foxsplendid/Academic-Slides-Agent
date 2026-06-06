## ADDED Requirements

### Requirement: Per-run output folder
The compile node SHALL write each run's artifacts under a per-run folder — the compiled `.pptx`, the
`deck.json`, and a human-readable `deck.md` — so multiple runs on the same paper are isolated and
comparable.

#### Scenario: A run emits a markdown rendering
- **WHEN** a run is compiled
- **THEN** its run folder contains the `.pptx` and a `deck.md` rendering of the deck
