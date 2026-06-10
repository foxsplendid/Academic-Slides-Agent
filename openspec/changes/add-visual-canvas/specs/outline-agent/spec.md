## ADDED Requirements

### Requirement: Premium canvas planning and authoring
When the premium option is set, the skeleton MAY plan canvas pages for the most valuable slides and
the expansion SHALL author them under the canvas contract (palette, fonts, line-per-text, evidence-
only numbers) with guard-validated retries; an unfixable canvas SHALL degrade to a regular content
page rather than fail the run.

#### Scenario: Canvas plan routes to the canvas prompt
- **WHEN** a premium skeleton plans a canvas slide
- **THEN** its expansion uses the canvas authoring system prompt and the result passes the guard

#### Scenario: Unfixable canvas degrades
- **WHEN** every canvas attempt fails the guard
- **THEN** the slide is regenerated as a bullet-evidence page
