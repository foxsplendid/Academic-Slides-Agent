## Why

Real papers arrive with supplementary data — Excel/CSV sheets, zip archives, and the paper PDF.
The high-density experimental data lives in those attachments. We need to ingest them into a
provenance-tagged **Evidence Pool** (anti-hallucination) and into native `TableBlock`s. Structured
data (Excel/CSV) is the easy, lossless, high-value path; PDF tables are best-effort. MVP step 3
(docs/SPEC.md §6.1, §10).

## What Changes

- Add `packages/ingestion/` — `ingest(*paths) -> IngestResult` (`assets: list[EvidenceAsset]`,
  `tables: list[TableBlock]`), routing by file type:
  - `.xlsx`/`.csv` → `TableBlock` per sheet/file (lossless) + a `table` `EvidenceAsset`.
  - `.zip` → unpack and **recurse** on members; provenance tagged `archive.zip!member`.
  - `.pdf` → page text → `section_text` asset; tables → **best-effort** `TableBlock` (pdfplumber).
  - images → `figure` asset.
  - unknown types → skipped.
- Every asset carries **provenance** (`source` + `locator` like `{"sheet": ...}` / `{"page": ...}`).

## Capabilities

### New Capabilities
- `ingestion`: normalize heterogeneous inputs (spreadsheets, archives, PDFs, images) into a
  provenance-tagged Evidence Pool and ready-to-use `TableBlock`s.

### Modified Capabilities
<!-- consumes slide-ir's EvidenceAsset/TableBlock; no spec change there -->

## Non-goals

- Deep PDF table reconstruction / OCR (best-effort only).
- Semantic interpretation or summarization of data (that is the agents' job, later).
- Resolving figure assets into slides (Evidence-Pool → slide wiring is a later change).

## Impact

- New package `packages/ingestion/`. New dependencies: **`openpyxl` (MIT)** + **`pdfplumber` (MIT)**.
- **License hygiene:** PDF handled by `pdfplumber` (pdfminer.six, MIT) — **not PyMuPDF (AGPL)**.
  CSV via stdlib `csv`; archives via stdlib `zipfile`.
