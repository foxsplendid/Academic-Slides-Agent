## Why

Multi-file input already works (router + multipart upload + `<input multiple>`), so a user can upload
`paper.pdf` + `supp.xlsx` + `data.zip` today. But the supplementary **data never reaches content
generation**: the two-stage expander feeds only a slide's section text, so tables (the whole point of
supplements) are invisible to per-slide expansion and charts. This change closes that gap so figures,
discussion, and charts can be built from supplementary data.

## What Changes

- **Tables reach per-slide expansion.** The skeleton plan gains `table_refs` (which tables a slide
  uses); `build_deck_detailed` passes the ingested `tables` to `_expand_slide`, which injects the
  referenced tables' **actual data** (header + rows, a generous cap with a "...N more rows" note) so a
  slide can chart/discuss real numbers.
- **Richer table view in the digest.** Tables are listed with an index, source file, column names, and
  row count so the planner can choose and reference them.
- **Zip threads the workspace.** `ingest_zip(*, workspace=)` forwards it to nested members so a PDF or
  image inside a supplementary archive still gets MinerU / figure extraction.
- **Frontend: supplementary-aware.** The picker copy becomes "主论文 PDF + 补充材料(Excel/CSV/zip/
  图)" and, after upload, shows per-type ingestion counts (files / tables / figures). The upload
  response returns those counts.

## Capabilities

### Modified Capabilities
- `ingestion`: zip forwards the workspace to members.
- `outline-agent`: per-slide expansion receives the referenced data tables (with a high row cap).
- `web-ui`: supplementary-aware picker copy + per-type ingestion counts from the upload response.

## Non-goals

- Tagging inputs as main-vs-supplement roles in the Evidence Pool (the user chose a UI-copy hint
  instead). Streaming/lazy loading of huge datasets; we cap rows with a note.

## Impact

- `outline.py` (`serialize_table`, table-aware digest), `deepen.py` (`table_refs` → expand prompt),
  `archive.py` + `router.py` (zip workspace), `app.py` (upload counts), `apps/web` (copy + counts).
  No new deps. Verified with a synthetic supplementary `.xlsx` feeding a chart.
