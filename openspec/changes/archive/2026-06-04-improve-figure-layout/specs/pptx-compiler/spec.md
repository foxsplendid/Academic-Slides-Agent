## ADDED Requirements

### Requirement: Aspect-preserving figure layout
The compiler SHALL render a figure image fitted within its region preserving aspect ratio (no
distortion, no overflow) and centered, and SHALL allocate more of a slide's content area to a figure
block than to a text block.

#### Scenario: A figure is contained and centered
- **WHEN** a slide with a resolvable figure is compiled
- **THEN** the picture's width does not exceed the content width and its height does not exceed its
  allocated region, and it is horizontally centered

#### Scenario: A figure gets more room than bullets
- **WHEN** a slide has one figure block and one bullets block
- **THEN** the figure's region is taller than the bullets' region
