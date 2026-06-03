## Context

Per docs/SPEC.md §6.1, ingestion prioritizes structured supplementary data (Excel/CSV) — easy and
lossless — and treats PDF tables as best-effort. Outputs feed the Evidence Pool (`EvidenceAsset`)
and the compiler (`TableBlock`). This layer is pure extraction: no AI, no interpretation.

## Goals / Non-Goals

**Goals:**
- `ingest(*paths) -> IngestResult` with `assets` (Evidence Pool) + `tables` (ready `TableBlock`s).
- Lossless spreadsheet ingestion; recursive archive routing; best-effort PDF text/tables.
- Provenance on every asset.

**Non-Goals:**
- Deep PDF table reconstruction / OCR; semantic summarization; figure-to-slide wiring.

## Decisions

- **`openpyxl` (MIT) + stdlib `csv`, not pandas.** Cells are read as strings (TableBlock is
  `list[str]`); avoids pulling pandas just to stringify. Lighter, sufficient.
- **`pdfplumber` (MIT) for PDF, not PyMuPDF/`fitz` (AGPL) or MinerU (custom license).** Keeps the
  dependency tree fully permissive — a hard SPEC §2 constraint.
- **`IngestResult(assets, tables)`** rather than extending `EvidenceAsset` to hold table data —
  avoids modifying the `slide-ir` capability. Table assets reference their `TableBlock` via
  `content_ref = "table:<index>"`; `merge()` re-bases indices so combined results stay consistent.
- **Empty rows dropped, ragged rows padded** to the header width — defensive normalization for
  messy real-world sheets.

## Risks / Trade-offs

- [PDF table extraction is unreliable on borderless/merged tables] → best-effort + `needs_human_check=True`
  on the TableBlock; the Hard-Stop review (a later change) is where the human corrects it.
- [No type inference (everything is a string)] → fine for slides; downstream agents/format layers
  can refine. Avoids pandas weight.
- [Huge sheets produce huge tables] → faithful extraction here; trimming/summarization is the
  agents' responsibility, not ingestion's.
