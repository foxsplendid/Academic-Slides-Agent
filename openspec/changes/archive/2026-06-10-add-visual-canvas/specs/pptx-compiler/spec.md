## ADDED Requirements

### Requirement: Canvas guard and editable injection
The compiler SHALL validate canvas SVG against a closed ban list (scripts, foreignObject, animation,
media, images, external references) and the canonical viewBox, repair it with deterministic finalize
passes, convert it to native DrawingML text and vectors, and swap it into the saved package — never
rasterizing, never failing the deck on a bad canvas.

#### Scenario: Valid canvas becomes editable shapes
- **WHEN** a deck with a guard-clean canvas slide is compiled
- **THEN** the canvas page contains native editable text shapes from the SVG

#### Scenario: Invalid canvas fails open
- **WHEN** a canvas contains a banned element
- **THEN** the deck still compiles and the canvas is not injected
