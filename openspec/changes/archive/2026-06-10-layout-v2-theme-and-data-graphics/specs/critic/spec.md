## ADDED Requirements

### Requirement: Figure-led layout consistency
The critic SHALL flag any figure-led layout (`figure_caption`, `figure_left`, `big_figure`,
`figure_grid`) that carries no figure block, naming the slide for repair.

#### Scenario: figure_left without a figure is flagged
- **WHEN** a `figure_left` slide has no figure block
- **THEN** a repair-routable finding names that slide
