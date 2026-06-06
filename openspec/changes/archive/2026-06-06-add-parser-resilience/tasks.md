## 1. Quality assessment

- [x] 1.1 `ingestion/quality.py`: `assess_quality(result)` → {text_chars, text_pages, figures, tables, adequate, warnings}
- [x] 1.2 `IngestResult.warnings: list[str]`; `merge` extends it

## 2. Cascade

- [x] 2.1 Router `_ingest_pdf`: ordered backends (mineru→docling→pdfplumber); descend when not adequate; keep best
- [x] 2.2 `ASA_PDF_PARSER` forces a single backend (no cascade)
- [x] 2.3 Record parser used + warnings on the result

## 3. Docling backend (optional)

- [x] 3.1 `ingestion/docling_parser.py`: lazy-import Docling → Evidence Pool (skipped if not installed)
- [x] 3.2 Optional extra in pyproject; NOTICE entry

## 4. Surface + tests

- [x] 4.1 Upload response returns parse quality + warnings; web UI shows a warning when thin
- [x] 4.2 Unit: `assess_quality` flags a thin parse; cascade descends mineru→pdfplumber on poor output
- [x] 4.3 Full suite green
