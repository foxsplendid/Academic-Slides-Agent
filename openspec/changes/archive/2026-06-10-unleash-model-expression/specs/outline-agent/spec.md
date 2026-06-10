## MODIFIED Requirements

### Requirement: Deck-level design planning and density contracts
By default the planner SHALL decide the page count and per-slide density from the paper's content
(one page per point worth a full treatment); explicit detail levels SHALL act as soft targets the
model may exceed for content reasons. The skeleton SHALL assign figures as a list per slide so
multi-figure layouts are expressible, and the expansion SHALL follow the skeleton's planned figure
layout.

#### Scenario: Auto density
- **WHEN** no detail level is chosen
- **THEN** the prompts carry the model-decided density principle and no page quota

#### Scenario: figure_grid carries its figures
- **WHEN** the skeleton plans a figure_grid slide with three figure ids
- **THEN** the expansion prompt lists all three with caption hints
