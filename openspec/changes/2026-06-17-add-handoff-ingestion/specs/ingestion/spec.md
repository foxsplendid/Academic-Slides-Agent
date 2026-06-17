## ADDED Requirements

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
