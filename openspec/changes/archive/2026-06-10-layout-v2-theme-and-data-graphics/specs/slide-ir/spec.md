## ADDED Requirements

### Requirement: Composition layout vocabulary
The IR SHALL provide layout values for the recurring academic compositions: `figure_left` (figure
left, text right), `two_content` (two blocks side by side), `figure_grid` (2-4 figures in a grid),
and `big_figure` (one dominant figure), in addition to the existing layouts.

#### Scenario: New layouts validate
- **WHEN** a slide declares `layout_type: "figure_grid"`
- **THEN** it passes IR validation
