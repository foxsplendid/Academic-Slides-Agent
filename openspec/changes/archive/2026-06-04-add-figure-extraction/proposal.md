## Why

The reference 组会 deck is figure-driven (15 images across 8 slides); our decks are text-only because
ingestion extracts no figures. Probing the real paper showed its figures are **vector** charts (Fig.1
has zero embedded raster images), so pulling embedded images is useless — we must **render** figure
regions. This adds caption-anchored figure rendering so real figures flow into the Evidence Pool and
get embedded natively in the .pptx.

## What Changes

- New **`figure-extraction`** capability in ingestion: locate `Fig. N` / `Figure N` captions, infer
  each figure's region (the caption's horizontal band, from the body-prose line above it down to the
  caption), and **render that region to PNG with pypdfium2** (PDFium = BSD; never PyMuPDF/AGPL). Each
  figure becomes an `EvidenceAsset(kind="figure")` whose `content_ref` is the PNG path, with the
  caption and page in `locator`.
- `ingest`/`ingest_path`/`ingest_pdf` gain an optional `workspace` dir where figure PNGs are written.
- The evidence digest lists each figure's `asset_id` **and caption** so the planner can place it.
- **Compiler** gains an `asset_resolver` (asset_id → file path) so a `figure` block renders the real
  rendered image; the graph builds the resolver from the Evidence Pool. Unresolved ids still fall back
  to the text placeholder.

## Capabilities

### New Capabilities
- `figure-extraction`: caption-anchored rendering of (vector or raster) PDF figures into the Evidence
  Pool as native image assets.

### Modified Capabilities
- `pptx-compiler`: resolve `figure` asset_ids to rendered image files via an `asset_resolver`.

## Non-goals

- Pixel-perfect figure cropping or panel splitting (the region is a best-effort caption-anchored box).
- OCR of figure text; multi-figure-per-caption layouts; rotated pages.

## Impact

- New `ingestion/figures.py`; `pdf.py`/`router.py` thread a `workspace`. `pypdfium2` (already present
  via pdfplumber) becomes an explicit dep + NOTICE entry; Pillow likewise. Compiler `compile_deck`
  /`render_figure` gain `asset_resolver`; the graph passes it. Verified on the real Zhang 2026 PDF
  (Fig.1–3 rendered and embedded).
