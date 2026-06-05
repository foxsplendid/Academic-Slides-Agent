## ADDED Requirements

### Requirement: Supplementary data reaches per-slide expansion
The two-stage builder SHALL let a slide reference ingested data tables (`table_refs`) and SHALL inject
those tables' actual data (header + rows, capped with a remainder note) into the slide's expansion
prompt, so a slide can build a chart or discussion from supplementary data.

#### Scenario: A referenced table's data is given to expansion
- **WHEN** a slide plan lists a `table_refs` index and the builder expands that slide
- **THEN** the expansion prompt contains that table's column headers and data rows
