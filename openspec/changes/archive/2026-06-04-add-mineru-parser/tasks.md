## 1. MinerU client

- [x] 1.1 `ingestion/mineru.py`: v4 flow — request upload URL, PUT file, poll batch results, download zip
- [x] 1.2 Unzip into the workspace; locate `*_content_list.json` + images dir

## 2. Parser (pure, testable)

- [x] 2.1 `parse_mineru_content_list(blocks, assets_dir, source, workspace)` -> `IngestResult`
- [x] 2.2 text/heading -> reading-order `section_text`; equation -> inline LaTeX
- [x] 2.3 table HTML -> `TableBlock` (+ caption); image -> `figure` asset (copied into workspace) with caption

## 3. Routing & config

- [x] 3.1 `router.ingest_path`: use MinerU when `MINERU_API_KEY` set + workspace present, else pdfplumber
- [x] 3.2 `ASA_PDF_PARSER=auto|mineru|pdfplumber` override; MinerU failure falls back gracefully
- [x] 3.3 Reuse `MINERU_API_KEY`/`MINERU_API_URL` into gitignored `.env` (not committed)

## 4. Verify

- [x] 4.1 Unit: `parse_mineru_content_list` fixture -> text/table/figure assets (no network)
- [x] 4.2 Real run: Zhang 2026 via live MinerU API -> cleaner evidence than pdfplumber; deck + figures
- [x] 4.3 Full suite green; `.env` not staged
