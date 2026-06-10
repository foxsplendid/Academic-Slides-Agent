## ADDED Requirements

### Requirement: TOC and ending rendering
The compiler SHALL render a `toc` slide as a numbered agenda (accent number chips + section titles)
and an `ending` slide as a centered closing divider in the deck theme.

#### Scenario: TOC renders numbered chips
- **WHEN** a toc slide with four agenda items compiles
- **THEN** four accent-colored numbered chips render beside the titles
