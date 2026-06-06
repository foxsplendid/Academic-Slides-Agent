## ADDED Requirements

### Requirement: Diagrams from the paper's logic
The planner SHALL emit a `DiagramBlock` only with nodes/edges that reflect a structure present in the
evidence and SHALL NOT fabricate relationships (it may visualize a process, comparison, or
relationship the paper actually describes).

#### Scenario: Prompt forbids fabricated relationships
- **WHEN** the planner prompts are produced
- **THEN** they instruct that diagram nodes/edges must come from the paper and must not be invented
