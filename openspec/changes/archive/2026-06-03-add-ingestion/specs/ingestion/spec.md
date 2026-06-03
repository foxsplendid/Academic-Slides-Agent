## ADDED Requirements

### Requirement: Ingest spreadsheets into native tables
The system SHALL convert each `.xlsx` worksheet and each `.csv` file into a `TableBlock` whose
`columns` come from the first row and whose `rows` preserve the remaining rows.

#### Scenario: CSV becomes a table
- **WHEN** a CSV with a header row and N data rows is ingested
- **THEN** the result contains a TableBlock with those columns and N data rows

#### Scenario: Each Excel sheet becomes a table
- **WHEN** an `.xlsx` workbook with 2 non-empty sheets is ingested
- **THEN** the result contains 2 TableBlocks, one per sheet

### Requirement: Recurse into archives
The system SHALL unpack `.zip` archives and ingest each member by its own file type.

#### Scenario: Zip members are ingested
- **WHEN** a zip containing a CSV and an XLSX is ingested
- **THEN** the result contains the tables from both members

### Requirement: Best-effort PDF extraction
The system SHALL extract text from each PDF page as a `section_text` asset and attempt table
extraction, without failing on imperfect tables.

#### Scenario: PDF page text becomes an asset
- **WHEN** a PDF containing text is ingested
- **THEN** the result contains at least one `section_text` EvidenceAsset whose content includes that text

### Requirement: Provenance on every asset
Every produced `EvidenceAsset` SHALL record its `source` file and a `locator` identifying its
origin within that source (e.g. sheet name or page number).

#### Scenario: Asset records source and locator
- **WHEN** an `.xlsx` sheet is ingested
- **THEN** its EvidenceAsset records the file as `source` and the sheet name in `locator`

### Requirement: Route by type and combine inputs
The system SHALL dispatch each input by file extension, skip unknown types, and combine multiple
inputs into one result with consistent table references.

#### Scenario: Unknown type is skipped
- **WHEN** a `.txt` file is ingested
- **THEN** it contributes no assets or tables (and does not raise)

#### Scenario: Multiple inputs combine
- **WHEN** two spreadsheets are ingested together
- **THEN** the result contains the tables from both
