# CLAUDE.md — Academic-Slides-Agent (Lectern)

Part of the **Scriptorium suite** — its reporting tool. Turns a paper (PDF) or a Steward **handoff package** into a **native, editable** `.pptx`. **Apache-2.0**, deliberately avoiding AGPL; positioned to **replace PPT-Agent** as the suite's slide generator.

> Past decisions & cross-project history live in the **Provenance** memory hub — query via prov-mcp (`get_current_context`, `search_brain`). Much of ASA's design happened in the catch-all `Dialogue` session, so consult Provenance + this file + docs/SPEC.md rather than expect local chat history here.

## What this is
Pipeline: ingest paper/handoff → **evidence pool** → **human-approved outline** (gate) → editable `.pptx`. Python monorepo (uv/hatchling editable workspace under `packages/` + `apps/`) + a React/Vite web UI (`apps/web`). Python **≥ 3.12**. Spec: `docs/SPEC.md` (v0.5.5). API: `python -m asa_api` (default 127.0.0.1:8000; routes `POST /jobs/upload`, `GET /jobs/{id}/stream`, `POST /jobs/{id}/approve`, `GET /jobs/{id}/download`). Providers: openai | deepseek | anthropic. Styles: academic | modern_teal.

## Key decisions (don't relitigate)
- **Native editable pptx**, not rendered images — slides stay editable in PowerPoint.
- **Human-approved outline gate**: never jump straight to a finished deck; the outline is reviewed first.
- **Consumes** the `handoff/1.0` package (single/multi-paper) staged by `steward pick` — does not touch Zotero directly.
- Apache-2.0 + NOTICE; the one vendored snapshot (`svg2pptx`, MIT) is attributed.

## Conventions
- Code/comments in English. Packages: `asa-{slide-ir, pptx-compiler, formula, ingestion, agents, providers, svg2pptx, api}`.
- Remote: `foxsplendid/Academic-Slides-Agent` (move into scriptorium-suite org is pending). See README.md / README.zh.md.
