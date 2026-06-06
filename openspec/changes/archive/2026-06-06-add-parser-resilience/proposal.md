## Why

PDF parsing over-relies on MinerU: today it only falls back to pdfplumber when MinerU **raises**, not
when it returns thin/empty output, and a bad source PDF (scanned, encrypted) silently degrades the
whole deck. We add a quality-gated parser cascade with a license-clean academic backup, plus parse
health surfaced to the user before they spend LLM calls. (Parser shortlist filtered from the user's
`pdf_parsers_comparison.md`: keep MIT/Apache/arms-length; reject AGPL PyMuPDF and GPL Marker.)

## What Changes

- **Quality-gated cascade.** `assess_quality(result)` scores a parse (text chars, pages, figures,
  tables) and decides "adequate". The PDF router tries backends in order and **descends on poor output,
  not just on exceptions**, keeping the best result if none is adequate.
- **Backends (all license-clean):** `MinerU` cloud API (Tier-1) → **Docling** (MIT, optional plugin,
  Tier-2, used only if installed) → `pdfplumber` (MIT, always-available Tier-3). `ASA_PDF_PARSER`
  forces a single backend.
- **Health + warnings.** `IngestResult.warnings` carries notes ("解析文本过少,可能是扫描件/解析失败");
  the upload response returns parse quality + warnings; the web UI shows a warning when a parse looks
  thin.

## Capabilities

### Modified Capabilities
- `ingestion`: quality-gated multi-backend PDF cascade + optional Docling backend + parse warnings.
- `web-ui`: surface parse quality / warnings after upload.

## Non-goals

- Grobid (academic structure/references) and Nougat (formula specialist) backends — left as future
  optional plugins. Local MinerU. OCR ourselves (we detect & warn; MinerU's OCR is the OCR path).

## Impact

- New `ingestion/quality.py` + `ingestion/docling_parser.py` (lazy/optional); `router.py` cascade;
  `models.py` gains `IngestResult.warnings`; `app.py` upload returns quality+warnings; `apps/web` shows
  warnings. Docling is an optional extra (no new hard dep). Verified: cascade descends on a thin parse;
  warnings surface.
