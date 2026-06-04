## Why

Our pdfplumber pipeline (two-column crop + caption-anchored figure render) is a no-better-tool
fallback and is lossy: jumbled reading order, no formulas, noisy tables, imprecise figure crops. This
directly caps deck quality (a 组会 talk needs clean full text, real formulas/tables, and precise
figures). **MinerU** does layout-aware parsing far better, and — critically — its **cloud API**
(`mineru.net/api/v4`) is an arms-length HTTP service, so calling it does **not** make our Apache code a
derivative of MinerU (license-clean, like calling DeepSeek). MinerU also relicensed off AGPL-3.0.

## What Changes

- New **MinerU parsing backend** (`ingestion/mineru.py`): submit a PDF via the v4 batch upload flow
  (`POST /file-urls/batch` → `PUT` upload → poll `GET /extract-results/batch/{id}` → download
  `full_zip_url`), unzip, and parse `*_content_list.json` into the Evidence Pool — clean reading-order
  `section_text` (headings + inline formulas as LaTeX), structured `TableBlock`s from HTML tables, and
  `figure` assets from MinerU's precise image crops with real captions.
- **Routing:** PDF ingestion uses MinerU when `MINERU_API_KEY` is set and a workspace is available;
  otherwise it falls back to pdfplumber. `ASA_PDF_PARSER=auto|mineru|pdfplumber` overrides. We write
  our own thin client against MinerU's public API docs (no PPT-Agent code copied).
- The MinerU token/URL are reused from PPT-Agent into this project's **gitignored `.env`**.

## Capabilities

### Modified Capabilities
- `ingestion`: add a high-fidelity MinerU cloud-API PDF backend (clean text/formulas/tables/figures),
  selected by env, with pdfplumber as the offline fallback.

## Non-goals

- Local MinerU deployment (GPU). Cloud API only this round.
- Content-depth changes in the planner; better evidence is expected to lift quality on its own.

## Impact

- New `ingestion/mineru.py` (network flow + a pure `parse_mineru_content_list` parser that is unit
  tested with a fixture). `router.py` gains env-based backend selection. Uses stdlib `urllib`/`zipfile`
  (no new deps). Verified end-to-end on the real Zhang 2026 PDF via the live API.
