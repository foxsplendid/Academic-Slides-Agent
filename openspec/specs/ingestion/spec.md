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

### Requirement: Quality-gated parser cascade
PDF ingestion SHALL assess parse quality and try backends in order (MinerU → Docling if available →
pdfplumber), descending to the next backend when a result is inadequate (not only when a backend
raises), and returning the best available result. A forced `ASA_PDF_PARSER` SHALL use a single backend.

#### Scenario: A thin parse descends to the next backend
- **WHEN** the first backend returns an inadequate result (e.g. near-empty text)
- **THEN** ingestion falls through to the next backend and returns a result

### Requirement: Parse warnings
Ingestion SHALL attach warnings when a parse looks unhealthy (very little text — likely scanned or
failed), carried on the result so callers can surface them.

#### Scenario: A near-empty parse is flagged
- **WHEN** a PDF parse yields almost no text
- **THEN** the result carries a warning noting the thin parse

### Requirement: Content-addressed parse cache
When a cache directory is provided, PDF ingestion SHALL key a parse by the file's content hash (plus
parser) and reuse a cached Evidence Pool on a hit instead of re-parsing, with figure images persisted
in the cache and referenced by stable paths.

#### Scenario: Re-ingesting the same file hits the cache
- **WHEN** the same PDF is ingested twice with the same cache directory
- **THEN** the underlying parse runs only once and the second call returns the cached result

### Requirement: Optional composite-figure splitting
When enabled (`ASA_SPLIT_FIGURES`), ingestion SHALL detect full-span near-white gutters in a figure and
emit each sub-panel as a sibling `figure` asset (keeping the whole figure), using a deterministic,
license-clean (Pillow-only) method that conservatively avoids splitting single-panel images. When
disabled it SHALL emit only the whole figure.

#### Scenario: A multi-panel figure splits into panels
- **WHEN** a 2×2-panel figure is ingested with `ASA_SPLIT_FIGURES` enabled
- **THEN** the result contains the whole figure plus four panel figure assets

#### Scenario: A single-panel figure is not split
- **WHEN** a single-panel image is processed
- **THEN** no panel assets are produced

### Requirement: Ingest a Scriptorium handoff package
The system SHALL recognize a `handoff/1.x` package — a directory containing a `meta.json` whose
`schema_version` begins with `handoff/` — and ingest each paper it references into the Evidence Pool,
reusing the standard PDF backends (MinerU → Docling → pdfplumber, cached). A paper without a resolvable
PDF SHALL still contribute its metadata as evidence. Detection SHALL be best-effort: a malformed or
non-handoff directory SHALL NOT raise.

#### Scenario: A handoff directory is routed to the handoff backend
- **WHEN** a directory containing a `meta.json` with `schema_version` "handoff/1.0" is ingested
- **THEN** it is dispatched to the handoff backend rather than skipped as an unknown type

#### Scenario: A plain directory is skipped
- **WHEN** a directory without a `meta.json` is ingested
- **THEN** it contributes no assets or tables and does not raise

#### Scenario: A paper PDF flows through the standard backends
- **WHEN** a handoff package references a PDF that exists on disk
- **THEN** the result contains the `section_text` assets extracted from that PDF

### Requirement: Bibliographic metadata becomes provenance
The handoff backend SHALL inject each paper's `title`, `authors`, `year`, and `doi` from `meta.json`
into the Evidence Pool as provenance: at minimum a `section_text` "report basis" asset stating what the
report is based on, plus per-paper metadata carried on assets' `source`/`locator`, so the speaker notes
can state "本报告基于 …".

#### Scenario: meta fields surface as a basis asset
- **WHEN** a handoff package with a title, authors, year, and doi is ingested
- **THEN** the result contains a `section_text` asset whose content names the title and authors and
  whose locator records the doi and year

### Requirement: Multi-paper handoff packages
The handoff backend SHALL support a `papers` array (handoff/1.1) so one package can carry multiple
PDFs + metadata for a literature-synthesis report, and SHALL also accept a single-paper handoff/1.0
package (top-level fields = one paper) for backward compatibility. Across one package every produced
asset SHALL have a collision-free `asset_id`.

#### Scenario: A multi-paper package yields per-paper evidence
- **WHEN** a handoff/1.1 package lists two papers
- **THEN** the result contains a report-basis asset that names both papers and a metadata asset per
  paper, and all produced asset ids are unique

#### Scenario: A single-paper handoff/1.0 package still works
- **WHEN** a directory has a handoff/1.0 `meta.json` with top-level `title` (and optional `pdfFilename`)
  and no `papers` array
- **THEN** it is ingested as a one-paper report

### Requirement: Report type
The handoff backend SHALL read `report_type` (`literature` | `experiment`, default `literature`) and
record it on the report-basis asset's `locator` so downstream framing can adapt.

#### Scenario: report_type defaults to literature
- **WHEN** a handoff `meta.json` omits `report_type`
- **THEN** the report-basis asset's locator records `report_type` "literature"

