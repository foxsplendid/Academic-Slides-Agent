## ADDED Requirements

### Requirement: Diagram edge validation
The critic SHALL flag a diagram edge whose `source` or `target` does not match a defined node id.

#### Scenario: A dangling edge is flagged
- **WHEN** a diagram has an edge referencing a node id not present in its nodes
- **THEN** the critic reports the dangling edge
