# ingestion Specification

## Purpose
TBD - created by archiving change add-ingestion. Update Purpose after archive.
## Requirements
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

### Requirement: Column-aware PDF text
PDF text extraction SHALL detect a two-column page layout and extract each column separately so the
reading order is preserved (columns are not interleaved).

#### Scenario: Two-column page is not interleaved
- **WHEN** a two-column page is ingested
- **THEN** the left column's text precedes the right column's text rather than line-by-line interleaving

### Requirement: Low-quality tables are dropped
Ingestion SHALL discard tables that carry no usable structure — no data rows, fewer than two columns,
or a majority of auto-generated `colN` headers — so noise does not reach the planner.

#### Scenario: A noise table is filtered out
- **WHEN** pdfplumber returns a table whose headers are mostly auto-named and which has no data rows
- **THEN** that table is not added to the ingestion result

### Requirement: High-fidelity MinerU PDF backend
When configured with a MinerU API key and a workspace, ingestion SHALL parse PDFs via the MinerU cloud
API and map its structured output into the Evidence Pool: reading-order `section_text` (with inline
formulas as LaTeX), `TableBlock`s from HTML tables, and `figure` assets from MinerU's image crops with
their captions. When no key is configured it SHALL fall back to the pdfplumber backend.

#### Scenario: MinerU structured output maps to the Evidence Pool
- **WHEN** a MinerU `content_list` with a heading, a paragraph, an HTML table, and a captioned image is
  parsed
- **THEN** the result contains a `section_text` asset, a `TableBlock`, and a `figure` asset whose
  `content_ref` is an existing image file with the caption recorded

#### Scenario: Backend selection falls back without a key
- **WHEN** a PDF is ingested with no `MINERU_API_KEY` configured
- **THEN** the pdfplumber backend is used and ingestion still succeeds

### Requirement: Archive members inherit the workspace
Zip ingestion SHALL forward the workspace to each extracted member, so a PDF or image inside a
supplementary archive receives the same high-fidelity processing (MinerU / figure extraction) as a
top-level input.

#### Scenario: A workspace flows into archive members
- **WHEN** a zip is ingested with a workspace
- **THEN** its members are ingested with that same workspace

