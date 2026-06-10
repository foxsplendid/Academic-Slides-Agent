## ADDED Requirements

### Requirement: General composition engine
The compiler SHALL arrange any composition of major visuals, bullet lists, one stat band and one
callout band into a designed layout (side-by-side, grids, top/bottom bands) rather than a vertical
stack; and SHALL provide a deterministic canvas geometry lint estimating text overflow and overlap.

#### Scenario: Four-block page composes
- **WHEN** a slide carries stat + diagram + bullets + callout
- **THEN** the stat band renders on top, the callout band at the bottom, and the diagram beside the bullets

#### Scenario: Overflowing canvas text is flagged
- **WHEN** a canvas text line extends past the canvas edge
- **THEN** the geometry lint reports it
