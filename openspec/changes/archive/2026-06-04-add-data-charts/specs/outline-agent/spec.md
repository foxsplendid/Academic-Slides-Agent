## ADDED Requirements

### Requirement: Charts only from evidence data
The planner MAY emit a `ChartBlock` to visualize quantitative results, but its values SHALL come from
data present in the evidence; the planner SHALL NOT fabricate chart numbers.

#### Scenario: Prompt forbids fabricated chart data
- **WHEN** the planner prompts are produced
- **THEN** they instruct that chart values must come from the evidence and must not be invented
