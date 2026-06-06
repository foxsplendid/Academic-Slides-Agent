## Why

The user re-uploads the same paper repeatedly to compare agent modes, re-running the expensive MinerU
parse each time (slow + API quota). They want the same file to land in one project folder (parse once,
shared) while each agent run stays isolated with its own outputs/markdown for easy comparison.

## What Changes

- **Content-addressed parse cache.** PDFs are keyed by `sha256(bytes)` + parser; a hit loads the cached
  Evidence Pool (figures copied into the cache, `content_ref` rewritten to stable cache paths) instead
  of re-parsing. Transparent: same upload → cache hit → fast, no MinerU call.
- **Project / run layout.** Cache lives under `<out_dir>/papers/<hash>/`; each generation run writes its
  outputs under `<out_dir>/runs/<job_id>/` — `out.pptx`, `deck.json`, and a human-readable **`deck.md`**
  (title + per-slide bullets/notes/blocks) so multiple agent runs on the same paper are isolated and
  diffable.

## Capabilities

### Modified Capabilities
- `ingestion`: a content-addressed parse cache (`cache_dir`) shared across runs.
- `orchestration`: the compile node writes per-run `out.pptx` + `deck.json` + `deck.md` under
  `runs/<job_id>/`.

## Non-goals

- A first-class "project" entity/API with listing/dedup of source files beyond the parse cache. Cache
  eviction/TTL. Cross-machine cache.

## Impact

- New `ingestion/cache.py`; `router.py`/`ingest` thread `cache_dir`; `graph.py` compile node writes the
  run folder (+ `deck_to_markdown`); `app.py` passes `cache_dir=<out_dir>/papers`. No new deps.
  Verified: ingesting the same PDF twice hits the cache (second parse skipped); a run emits `deck.md`.
