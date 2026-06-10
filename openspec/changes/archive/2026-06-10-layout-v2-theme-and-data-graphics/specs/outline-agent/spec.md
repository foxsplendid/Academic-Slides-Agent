## ADDED Requirements

### Requirement: Layout vocabulary in planning
The skeleton planner SHALL offer the full layout vocabulary (including figure_left, two_content,
figure_grid, big_figure) with usage guidance so consecutive figure slides can alternate composition.

#### Scenario: Planner may choose a grid
- **WHEN** the skeleton plans a slide comparing multiple subpanels
- **THEN** `figure_grid` is an expressible layout choice
