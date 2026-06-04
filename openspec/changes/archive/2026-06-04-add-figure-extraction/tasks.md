## 1. Figure extraction

- [x] 1.1 `ingestion/figures.py`: find `Fig. N`/`Figure N` captions; infer caption-band region above each
- [x] 1.2 Render the region to PNG with pypdfium2 (BSD); skip implausibly thin regions
- [x] 1.3 Emit `EvidenceAsset(kind="figure", content_ref=<png path>)` with caption + page in `locator`
- [x] 1.4 Thread `workspace` through `ingest`/`ingest_path`/`ingest_pdf`

## 2. Planner awareness

- [x] 2.1 Evidence digest lists figure `asset_id` + caption

## 3. Compiler resolution

- [x] 3.1 `compile_deck`/`render_figure` accept `asset_resolver` (asset_id -> path)
- [x] 3.2 Graph compile node builds the resolver from the Evidence Pool

## 4. Deps & verify

- [x] 4.1 Add `pypdfium2` + `Pillow` as explicit ingestion deps; record in NOTICE
- [x] 4.2 Unit: caption detection + region render produces a non-empty PNG asset (synthetic PDF)
- [x] 4.3 Unit: compiler embeds a resolved figure as a picture shape
- [x] 4.4 Real paper: Fig.1–3 rendered, referenced by the planner, embedded in the .pptx; full suite green
