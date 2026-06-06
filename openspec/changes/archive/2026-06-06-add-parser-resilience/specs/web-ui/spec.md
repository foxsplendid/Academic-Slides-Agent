## ADDED Requirements

### Requirement: Parse-quality feedback
The upload response SHALL include parse warnings, and the web UI SHALL show a warning when a parse
looks thin so the user can react before spending generation.

#### Scenario: A thin parse warns the user
- **WHEN** the upload response carries a parse warning
- **THEN** the UI displays that warning
