## ADDED Requirements

### Requirement: Layout monotony detection
The critic SHALL flag more than three consecutive content slides sharing one layout as a
repair-routable finding naming a slide inside the run; structural dividers and the TOC reset the run.

#### Scenario: A five-slide run is flagged
- **WHEN** five consecutive content slides share `bullet_evidence`
- **THEN** a finding names a slide in the run and suggests varying the composition
