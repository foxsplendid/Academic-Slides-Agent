## 1. Package setup

- [x] 1.1 Create `packages/ingestion/` package (`pyproject.toml`, `ingestion/`)
- [x] 1.2 Deps: `asa-slide-ir` (local), `openpyxl` (MIT), `pdfplumber` (MIT); record in `NOTICE`

## 2. Result model

- [x] 2.1 `IngestResult(assets: list[EvidenceAsset], tables: list[TableBlock])`
- [x] 2.2 `merge(other)` that re-bases `content_ref = "table:<index>"` references

## 3. Extractors

- [x] 3.1 `ingest_csv` — stdlib `csv` → TableBlock + asset
- [x] 3.2 `ingest_xlsx` — `openpyxl` (read-only, data-only) → one TableBlock + asset per sheet
- [x] 3.3 `ingest_pdf` — `pdfplumber`: page text → `section_text` asset; tables → best-effort TableBlock
- [x] 3.4 `ingest_zip` — `zipfile` unpack + recurse; tag provenance `archive!member`
- [x] 3.5 images → `figure` asset
- [x] 3.6 Normalize: drop empty rows, pad ragged rows, fill blank headers

## 4. Router

- [x] 4.1 `ingest_path(path)` dispatch by extension; unknown → empty result
- [x] 4.2 `ingest(*paths)` combine via `merge`

## 5. Tests

- [x] 5.1 CSV → table with correct columns/rows
- [x] 5.2 XLSX with 2 sheets → 2 tables; asset records sheet in `locator`
- [x] 5.3 Zip(csv+xlsx) → combined tables; source tagged with archive name
- [x] 5.4 PDF text → `section_text` asset containing the text (matplotlib-generated fixture)
- [x] 5.5 Image → `figure` asset; unknown `.txt` → empty; multi-input combine
