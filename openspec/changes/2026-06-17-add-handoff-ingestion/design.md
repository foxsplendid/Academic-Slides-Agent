# Design — handoff package ingestion

## Contract: `handoff/1.1` (proposed)

`handoff/1.0` (in `scriptorium-spec/schemas/handoff/v1.json`) describes **one** paper: top-level
`title/authors/year/doi/tldr/abstract/folders/pdfFilename`, one directory per handoff. Phase E needs
(a) a report kind and (b) multiple papers in one package. `v1.1` adds both **without breaking 1.0**:

- `report_type`: `"literature" | "experiment"` — optional, default `"literature"`.
- `papers`: optional array; each item has the same per-paper shape
  (`title` required; `authors/year/doi/tldr/abstract/pdfFilename/folders` optional). When present the
  package is a multi-source report and the **top-level `title` is the report title**.
- **Backward compatibility:** when `papers` is absent the top-level fields ARE the single paper — a
  `handoff/1.0` directory validates and ingests unchanged. The `schema_version` regex
  `^handoff/1\.[0-9]+$` already admits `handoff/1.1`.

Proposed `v1.1.json` (the artifact the **scriptorium-spec** repo — the coordination point — would
adopt; reproduced here so this change is self-contained):

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/scriptorium-suite/scriptorium-spec/blob/main/schemas/handoff/v1.1.json",
  "title": "Scriptorium Paper Handoff v1.1",
  "description": "Metadata sidecar (meta.json) staged next to one or more papers when handing a report from the library (Steward `pick`) to a downstream consumer such as Lectern. Single-paper: top-level fields describe the paper (1.0-compatible). Multi-paper: `papers[]` lists the sources and the top-level `title` is the report title.",
  "type": "object",
  "required": ["schema_version", "key", "title"],
  "properties": {
    "schema_version": { "type": "string", "pattern": "^handoff/1\\.[0-9]+$" },
    "key": { "type": "string", "pattern": "^[A-Z0-9]{8}$" },
    "report_type": { "enum": ["literature", "experiment"], "default": "literature" },
    "title": { "type": "string" },
    "authors": { "type": "array", "items": { "type": "string" } },
    "year": { "type": "string", "pattern": "^([0-9]{4})?$" },
    "doi": { "type": "string" },
    "tldr": { "type": "string" },
    "abstract": { "type": "string" },
    "folders": { "type": "array", "items": { "type": "string" } },
    "pdfFilename": { "type": "string", "description": "Staged PDF for the single-paper form." },
    "papers": {
      "type": "array",
      "description": "Multi-paper form. Each item is one source paper staged in the same directory.",
      "items": {
        "type": "object",
        "required": ["title"],
        "properties": {
          "title": { "type": "string" },
          "authors": { "type": "array", "items": { "type": "string" } },
          "year": { "type": "string", "pattern": "^([0-9]{4})?$" },
          "doi": { "type": "string" },
          "tldr": { "type": "string" },
          "abstract": { "type": "string" },
          "folders": { "type": "array", "items": { "type": "string" } },
          "pdfFilename": { "type": "string" }
        }
      }
    }
  }
}
```

> **Coordination note.** The contract is owned by `scriptorium-spec`, not this repo. Lectern parses
> defensively (best-effort, never raises on a slightly-off package) so a producer running ahead of or
> behind `v1.1` still works. Landing `v1.1.json` in scriptorium-spec + teaching Steward `pick` to emit
> `report_type`/`papers` is a separate, coordinated change tracked there.

## Detection — why a directory, not a new extension

A handoff package is a **directory** (`<staging>/<key>/{*.pdf, meta.json}`), so suffix routing skips
it (a directory has no suffix → today's `ingest_path` returns an empty result). The new branch fires
when `path.is_dir()` **and** `path/meta.json` exists **and** its `schema_version` starts with
`handoff/`. This is unambiguous and keeps plain directories (no meta.json) skipped as before.

Entry path: the local-path `POST /jobs {inputs: ["…/handoff/<key>"]}` already calls
`ingest(*inputs)` → `ingest_path(dir)`, so the branch is the only wiring needed — no app.py change.

## Paper normalization

`meta.json` → a list of paper dicts: use `papers[]` when present, else synthesize one paper from the
top-level fields (1.0). Each paper is resolved to a PDF by `pdfFilename` (relative to the package
dir); if absent or missing on disk, the paper still contributes metadata-only evidence (literature
reports often have just an abstract).

## Provenance injection

Two asset shapes, both `section_text` (so no IR/compiler change, planner reads them already):

1. **Report-basis asset** (`asset_id="report_basis"`): the "本报告基于 …" hook. Single paper →
   `本报告基于:<title> — <authors> (<year>). doi:<doi>`; multi → a numbered list of all sources.
   `locator` records `report_type`, `handoff_key`, and a compact `papers` list (machine-readable
   provenance). This is what lets the title-slide speaker notes cite the source.
2. **Per-paper metadata asset** (`asset_id="meta:<paper>"`): title/authors/year/doi/tldr/abstract as
   text, with the same fields on `locator` and `source` set to the PDF filename (or `meta.json`).

The metadata is **factual** (curated by Steward), not model-generated, so feeding it as evidence does
not risk hallucination — it is exactly the provenance the anti-hallucination design wants.

## Multi-paper id collisions

`pdf.py` derives `section_text` ids from `path.stem`; two papers with the same filename (or generic
names) would collide, and `compile`'s `{asset_id: content_ref}` resolver needs unique ids. So for a
multi-paper package each paper's ingested assets are **namespaced** with a `p{n}_` prefix on
`asset_id`. Single-paper packages keep ids verbatim (1.0 behavior). `table:<idx>` content-refs are
re-based by the existing `IngestResult.merge`.

## License

`handoff.py` uses only the stdlib (`json`, `pathlib`) and reuses existing ingestion. No new
dependency → Apache-2.0 gate unaffected.
