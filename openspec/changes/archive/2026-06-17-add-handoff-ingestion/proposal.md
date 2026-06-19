## Why

Lectern (this repo) is the report end of the Scriptorium suite. Steward's `pick` already stages a
**handoff package** — a directory holding a paper's PDF + a `meta.json` (title/authors/year/doi/
tldr/abstract/folders, contract `handoff/1.0`) — and can POST it to `/jobs/upload`. But ingestion
only knows file extensions (PDF/xlsx/csv/zip/image); it has **no concept of a handoff package**, so
the curated bibliographic metadata is thrown away and the deck cannot say "本报告基于 …".

Phase E of the workflow plan asks Lectern's entry to also eat handoff packages, and to grow beyond a
single paper: a **literature-synthesis** report (multiple papers in one package) or an **experiment**
report. That needs a contract bump to `handoff/1.1` (a `report_type` field + a `papers` array) and a
new ingestion backend that turns a package into ordinary Evidence Pool assets with the metadata
injected as provenance.

## What Changes

- New **handoff ingestion backend** (`ingestion/handoff.py`): given a handoff directory, read
  `meta.json`, resolve each paper's PDF, and ingest it through the **existing** PDF cascade
  (MinerU → Docling → pdfplumber, cached), so a handoff PDF gets the same high-fidelity processing as a
  direct upload. No PDF? The paper still contributes its title/abstract as evidence.
- **Router branch:** `ingest_path` recognizes a directory whose `meta.json` declares
  `schema_version: handoff/1.x` and dispatches it to the handoff backend (instead of skipping a
  suffix-less directory). Works through the existing local-path `POST /jobs {inputs:[dir]}` entry.
- **Provenance injection:** each paper's `title/authors/year/doi` become provenance — a `section_text`
  **report-basis** asset ("本报告基于 …", listing every source) plus per-paper metadata assets carrying
  the bibliographic fields on `source`/`locator`. The planner already reads `section_text`, so the
  basis surfaces in the digest and the title-slide speaker notes can cite the source with zero
  downstream change.
- **Contract upgrade `handoff/1.1`** (proposed; see design.md): adds `report_type:
  literature | experiment` (default `literature`) and an optional `papers[]` array for multi-paper
  packages, **backward-compatible** with `handoff/1.0` (top-level fields = one paper). The contract
  lives in the **scriptorium-spec** repo, which is the coordination point — this change proposes the
  schema; landing `v1.1.json` there is a separate, coordinated step.

## Capabilities

### Modified Capabilities
- `ingestion`: accept a Scriptorium `handoff/1.x` package (single- or multi-paper) as an input,
  reusing the standard PDF backends and injecting `meta.json` bibliographic fields as provenance.

## Non-goals

- No new HTTP endpoint and no `/jobs/upload` multipart change — the local-path `/jobs` entry already
  routes directory inputs through `ingest()`. A future `POST /jobs/from-handoff` is out of scope.
- No zipped-handoff detection (the package is a directory; zipping it is a separate concern).
- No Slide-IR change: the report basis/metadata are plain `section_text` assets, so the locked IR
  vocabulary and the compiler are untouched. A dedicated `reference` asset kind / references-slide
  layout stays future work.
- Not actually editing the scriptorium-spec repo's published schema (coordination point) — only
  proposing `handoff/1.1` here.

## Impact

- New `ingestion/handoff.py` (stdlib `json`/`pathlib` only — **no new dependency**, passes the
  Apache-2.0 gate); `router.py` gains a directory→handoff branch; `ingestion/__init__.py` exports the
  backend. Unit tests for detection, single/multi-paper, report_type, provenance, namespacing, and a
  real PDF flowing through. `docs/SPEC.md` §6.1 note + Changelog entry. Existing 262 tests unaffected.
