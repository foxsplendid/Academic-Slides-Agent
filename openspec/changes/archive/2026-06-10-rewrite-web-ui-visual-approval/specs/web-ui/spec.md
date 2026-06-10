## MODIFIED Requirements

### Requirement: Browser frontend drives the flow
The web UI SHALL be a three-view application (generate, visual approval, result) with a sidebar of
past jobs (status, open, delete), a generation view exposing per-job options (style, parser, opt-in
toggles) with staged live progress, a visual approval view presenting real rendered slide images with
approve and reject-with-feedback actions, and a result view with per-slide preview and download. It
SHALL remain export-first (no embedded editor) and degrade to a text outline when no renderer exists.

#### Scenario: Visual approval
- **WHEN** generation reaches the Hard-Stop on a host with a slide renderer
- **THEN** the user reviews rendered slide thumbnails and may approve or reject with feedback

#### Scenario: Renderer-less degradation
- **WHEN** no renderer is available
- **THEN** the approval view falls back to the text outline and approval still works

#### Scenario: Rejection replans live
- **WHEN** the user rejects with feedback
- **THEN** the replan progress streams in the UI and ends at a fresh visual approval
