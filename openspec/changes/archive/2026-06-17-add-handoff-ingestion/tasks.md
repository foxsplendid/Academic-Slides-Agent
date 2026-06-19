## 1. Contract

- [x] 1.1 Propose `handoff/1.1` (report_type + papers[], 1.0-compatible) in design.md
- [x] 1.2 Note scriptorium-spec as the coordination point; do not unilaterally land the schema there

## 2. Handoff backend

- [x] 2.1 `ingestion/handoff.py`: `is_handoff_dir(path)` detection (dir + meta.json + handoff/ schema)
- [x] 2.2 `ingest_handoff(path, *, workspace, cache_dir)`: read meta, normalize to a papers list
- [x] 2.3 Per paper: resolve & ingest the PDF via the standard cascade; metadata-only when no PDF
- [x] 2.4 Inject provenance: a `section_text` report-basis asset ("本报告基于 …") + per-paper metadata
- [x] 2.5 Namespace multi-paper asset ids (`p{n}_`) so the compile resolver stays collision-free
- [x] 2.6 Export from `ingestion/__init__.py`

## 3. Router

- [x] 3.1 `ingest_path` dispatches a handoff directory to the backend before suffix routing

## 4. Docs

- [x] 4.1 `docs/SPEC.md` §6.1 note + Changelog entry (no invariant changed)

## 5. Tests & verify

- [x] 5.1 Detection true/false; plain directory skipped (no raise)
- [x] 5.2 Single-paper 1.0 (metadata-only) → basis + metadata assets carry title/authors/year/doi
- [x] 5.3 Multi-paper 1.1 → basis lists both, per-paper metadata, unique ids, report_type recorded
- [x] 5.4 A real PDF in the package flows through (text reaches the pool, namespaced)
- [x] 5.5 Full suite green (no regression to the existing 262)
