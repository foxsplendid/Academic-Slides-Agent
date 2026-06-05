## ADDED Requirements

### Requirement: Archive members inherit the workspace
Zip ingestion SHALL forward the workspace to each extracted member, so a PDF or image inside a
supplementary archive receives the same high-fidelity processing (MinerU / figure extraction) as a
top-level input.

#### Scenario: A workspace flows into archive members
- **WHEN** a zip is ingested with a workspace
- **THEN** its members are ingested with that same workspace
