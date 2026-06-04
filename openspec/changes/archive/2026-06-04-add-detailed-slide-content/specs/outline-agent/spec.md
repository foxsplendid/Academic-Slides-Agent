## ADDED Requirements

### Requirement: Two-stage detailed deck
The planner SHALL offer a two-stage builder that first produces a slide skeleton (per slide: title,
layout, a focus, the evidence pages it draws on, and an optional figure) and then expands each slide
with a focused call given that slide's evidence at full resolution, yielding deeper per-slide content
(substantive bullets, an interpretation, and speaker notes) than the single-shot builder. The
assembled deck SHALL pass the strict IR boundary.

#### Scenario: Per-slide expansion deepens content
- **WHEN** the two-stage builder runs against evidence with the LLM scripted to return a skeleton and
  then a detailed slide per plan
- **THEN** it returns a valid `Deck` whose slides carry the expanded bullets and non-empty speaker notes

#### Scenario: A figure slide keeps its assigned figure
- **WHEN** the skeleton assigns a `figure_id` to a slide and that id exists in the Evidence Pool
- **THEN** the expanded slide contains a `figure` block with that `asset_id`
