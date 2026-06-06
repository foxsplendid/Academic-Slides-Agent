## ADDED Requirements

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
