## ADDED Requirements

### Requirement: Template upload and listing
The API SHALL accept a .pptx template upload, register its extracted style for immediate use,
persist it across restarts, and list available custom templates.

#### Scenario: Imported style drives a job
- **WHEN** a template is uploaded and a job is created with its style name
- **THEN** the run compiles successfully with that style
