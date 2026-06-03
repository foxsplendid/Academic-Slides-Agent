## ADDED Requirements

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
