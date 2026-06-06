## ADDED Requirements

### Requirement: Diagrams from the paper's logic
The planner MAY emit a `DiagramBlock` to visualize a process, comparison, or relationship, but its
nodes/edges SHALL reflect structure present in the evidence; the planner SHALL NOT fabricate
relationships.

#### Scenario: Prompt forbids fabricated relationships
- **WHEN** the planner prompts are produced
- **THEN** they instruct that diagram nodes/edges must come from the paper and must not be invented
