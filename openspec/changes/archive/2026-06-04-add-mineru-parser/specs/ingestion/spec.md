## ADDED Requirements

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
