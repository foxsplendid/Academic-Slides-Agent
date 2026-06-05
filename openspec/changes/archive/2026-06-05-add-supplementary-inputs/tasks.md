## 1. Tables → expansion

- [x] 1.1 `serialize_table(tb, *, max_rows, max_chars)` — header + rows with a "...N more rows" cap
- [x] 1.2 Digest lists tables with index + source + columns + row count
- [x] 1.3 Skeleton plan schema gains `table_refs`; skeleton prompt lists available tables
- [x] 1.4 `build_deck_detailed` passes `tables`; `_expand_slide` injects referenced tables' data; prompt says charts/discussion may use them

## 2. Zip workspace

- [x] 2.1 `ingest_zip(*, workspace=None)` forwards to recursive `ingest_path`; router passes workspace

## 3. Frontend + API

- [x] 3.1 Upload endpoint returns per-type counts (files / tables / figures)
- [x] 3.2 Picker copy "主论文 PDF + 补充材料(…)"; show ingestion counts after upload

## 4. Tests & verify

- [x] 4.1 Unit: `serialize_table` caps rows; zip forwards workspace; expand includes referenced table data
- [x] 4.2 Full suite green; real run: paper + synthetic supp `.xlsx` → table data reaches a slide / chart
