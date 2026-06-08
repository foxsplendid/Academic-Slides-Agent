## ADDED Requirements

### Requirement: Balanced figure/text height allocation
When a slide contains a figure, chart, or diagram together with a bullet block, the compiler SHALL cap
the combined height of those visual blocks so the text retains a readable share of the content area. A
slide whose only content is a visual block SHALL be unaffected by the cap.

#### Scenario: Figure shares a slide with bullets
- **WHEN** a slide has a figure and a bullet block
- **THEN** the figure's height is capped and the bullets receive the remaining share

#### Scenario: Figure-only slide is unaffected
- **WHEN** a slide's only content block is a figure
- **THEN** the figure uses the full content height
