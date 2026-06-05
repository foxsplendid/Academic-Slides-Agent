## ADDED Requirements

### Requirement: Supplementary-aware upload feedback
The upload response SHALL report per-type ingestion counts, and the web UI SHALL present a
supplementary-aware file picker and show those counts after upload.

#### Scenario: Upload reports what was ingested
- **WHEN** files are uploaded
- **THEN** the response includes counts of ingested files, tables, and figures
