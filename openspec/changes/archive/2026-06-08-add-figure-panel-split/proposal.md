## Why

Scientific figures are often one image stitched from sub-panels (A/B/C/D). Today a slide gets the whole
composite, wasting layout and forcing the reader to hunt the relevant panel. We add optional splitting
so individual panels become usable figure assets.

## What Changes

- **`ingestion/panels.py` `split_composite`**: band-based recursive X-Y-cut gutter detection —
  **Pillow-only, numpy-free** (per-row/col projection = mean of a 1-px BOX resize), AI-free &
  deterministic (fits the locked architecture). Conservative gates (min size, min gutter/panel
  fraction, area-reconstruction ≥60%) guard against over-segmentation.
- **MinerU integration (opt-in)**: when `ASA_SPLIT_FIGURES` is set, each figure is split and every
  panel becomes a **sibling `figure` EvidenceAsset** (`…:panelN`, with `parent`/`panel` in locator).
  The whole figure is kept too. Sibling assets flow end-to-end with **zero downstream changes** (the
  graph figure resolver + generic figure iteration pick them up).

## Capabilities

### Modified Capabilities
- `ingestion`: optional composite-figure panel splitting into sibling figure assets.

## Non-goals

- Panel-label (A/B/C) OCR; edge-based separation of touching/dark panels; per-panel captioning.
  Default-on (kept opt-in given ~82–85% accuracy / over-segmentation risk).

## Impact

- New `ingestion/panels.py`; `mineru.py` emits panels behind `ASA_SPLIT_FIGURES` (default off). No new
  deps (Pillow already required). Verified: synthetic 2×2→4 / 1×3→3 panels; single/small images don't
  split; opt-in gate off→1 figure, on→1+panels.
