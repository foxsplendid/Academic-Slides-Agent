## ADDED Requirements

### Requirement: Deterministic native diagram rendering
The compiler SHALL render a `DiagramBlock` by computing layout deterministically (no LLM coordinates)
and emitting native, editable PowerPoint shapes — rounded-rectangle nodes with text and connectors for
edges — for each supported `diagram_type`.

#### Scenario: A diagram becomes native shapes
- **WHEN** a slide with a `diagram` block of N nodes is compiled
- **THEN** the slide contains at least N native node shapes (and connectors for a flow's edges)
