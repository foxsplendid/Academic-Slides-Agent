## 1. Parse cache

- [x] 1.1 `ingestion/cache.py`: `cached_pdf(path, *, parser_key, cache_dir, parse_fn)` — sha256 key, load on hit, save on miss
- [x] 1.2 On save: copy figure images into the cache, rewrite `content_ref` to the cache path
- [x] 1.3 Thread `cache_dir` through `ingest`/`ingest_path`/`_ingest_pdf` (and zip members)

## 2. Run layout

- [x] 2.1 `deck_to_markdown(deck)` — title + per-slide bullets/notes/blocks
- [x] 2.2 Compile node writes `runs/<job_id>/` with `out.pptx` + `deck.json` + `deck.md`
- [x] 2.3 API passes `cache_dir=<out_dir>/papers`

## 3. Tests & verify

- [x] 3.1 Unit: same PDF ingested twice → second is a cache hit (parse_fn called once)
- [x] 3.2 Unit: `deck_to_markdown` renders slides/bullets; compile writes `deck.md`
- [x] 3.3 Full suite green; real run: re-ingest same paper is instant (no MinerU call)
