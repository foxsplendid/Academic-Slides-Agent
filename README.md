English | [中文](README.zh.md)

# Academic-Slides-Agent

> Turn a hard-science paper (PDF + supplementary data) into a rigorous, natively-editable `.pptx` — in one upload.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-275_passing-brightgreen.svg)](#status)
[![Spec](https://img.shields.io/badge/SPEC-v0.5.5-informational.svg)](docs/SPEC.md)

## Related / 相关文档

[README](README.md) · [中文 README.zh](README.zh.md) · [CLAUDE](CLAUDE.md) · [docs/SPEC](docs/SPEC.md)

**Suite / 套件:** [scriptorium-spec](https://github.com/scriptorium-suite/scriptorium-spec) (contract SSoT) · [steward](https://github.com/scriptorium-suite/steward) · [Provenance](https://github.com/foxsplendid/Provenance) · [Academic-Slides-Agent / Lectern](https://github.com/foxsplendid/Academic-Slides-Agent) · [.github](https://github.com/scriptorium-suite/.github)
> Contract facts are canonical in **scriptorium-spec/README**; other repos mirror, never fork them.

## Overview

Academic-Slides-Agent (aka *Lectern*) converts a hard-science paper — or a Scriptorium `handoff/1.x`
package — into a presentation deck for academic group meetings (组会) and conference talks. Unlike
business-deck generators (Gamma, Tome), it targets the hard-science bottlenecks: heavy LaTeX math and
chemistry, high-density experimental tables, real figures lifted from the paper, a strict academic
narrative, and bring-your-own-model privacy for unpublished data.

The single architectural rule is that the **LLM only ever emits a Pydantic-validated `Slide-IR`**
(structured JSON over a closed vocabulary); a separate **deterministic, AI-free compiler** turns that
IR into native `python-pptx` objects. The model supplies *semantics*, a deterministic engine computes
*geometry*, so every slide is a real PowerPoint object — editable text, native tables, native charts,
vector shapes — never a screenshot.

```
papers + ─▶ Ingestion ─▶ Evidence ─▶ Agents (LangGraph) ─▶ Slide-IR ─▶ Compiler ─▶ native
attachments   cascade      Pool       skeleton→expand→critic    (JSON)    (no AI)      .pptx
              + cache    (provenance)   ▲ human approval (Hard-Stop)
```

## Features

- **Ingestion** — multi-file input (PDF + Excel/CSV/zip/images) or a Scriptorium `handoff/1.x` package
  (a directory with `meta.json` + PDFs). Quality-gated parser cascade: **MinerU** cloud API →
  **Docling** (MIT, optional) → **pdfplumber** (always-available local fallback). Content-addressed
  parse cache, per-run isolation, composite-figure panel detection so multi-panel figures are never
  used as a whole.
- **Planning** — a two-stage planner (skeleton → per-slide focused expansion, expanded in parallel),
  producing an academic 组会 narrative with per-slide speaker notes, citations preserved, and every
  figure grounded to a real Evidence-Pool asset id. Page count and density are model-decided by default,
  with optional brief/normal/high presets.
- **Critic + human gate** — a deterministic, AI-free critic flags empty/overflowing slides, dangling
  figure references, broken diagram edges, near-duplicate titles, and TOC↔section mismatches, feeding a
  bounded repair loop. A LangGraph `interrupt()` **Hard-Stop** lets a human approve or reject the outline
  before compilation — reject a specific page by number and only that page is regenerated.
- **Native compiler (fully editable)** — Slide-IR → native python-pptx: CJK-aware bullets/tables;
  native `bar`/`line`/`scatter`/`pie` charts (incl. a predicted-vs-reference scatter with auto 1:1 line);
  diagrams (`flow`/`tree`/`cycle`/`comparison`/`pyramid`/`timeline`) from semantic nodes+edges (no
  coordinates); aspect-ratio-aware figure layout; tiered formula rendering (matplotlib → MathJax + mhchem
  Node sidecar → experimental native-editable OMML); deck chrome (section dividers, takeaway band,
  running header/footer); and a premium **VisualCanvas** tier (constrained SVG → editable vector via the
  vendored MIT SVG→DrawingML engine, with deterministic fallback).
- **Delivery** — FastAPI service (SSE streaming, durable background runs, resume) plus a React
  export-first web UI (upload → live progress → outline approval → download) with a full-screen viewer.
- **Privacy** — secrets live only in a local, gitignored `.env`; point the OpenAI-compatible base URL at
  a local Ollama/vLLM endpoint to keep unpublished data entirely on your own hardware.

## Installation

A Python monorepo of editable workspace packages (under `packages/` and `apps/`) plus a React web UI.
Requires **Python 3.12+** and Node.js (for the web UI and the MathJax formula sidecar).

```bash
# 1) Python deps — install the whole uv workspace editable in one command.
#    Creates .venv and installs every package under packages/ + apps/ plus the
#    shared dev tooling (pytest etc.). Adds the openai client; for Anthropic also
#    run:  uv pip install "anthropic>=0.40"
uv sync --all-packages

# 2) Configure — copy the template and fill in your own keys
cp .env.example .env        # then edit .env (it is gitignored — never commit real keys)
```

**One-click (Windows):** double-click [`start-dev.bat`](start-dev.bat) — it checks `.venv`/npm, installs
frontend deps on first run, starts the backend (`:8000`) and the Vite dev server (`:5173`) in their own
windows, and opens the browser.

## Usage

```bash
# Run the API
python -m asa_api           # serves on http://127.0.0.1:8000

# Run the web UI (separate terminal)
cd apps/web && npm install && npm run dev   # http://localhost:5173
```

Or drive the API directly: `POST /jobs/upload` (ingest inputs) → `GET /jobs/{id}/stream` (SSE) → review
the outline → `POST /jobs/{id}/approve` → `GET /jobs/{id}/download`.

**Headless CLI (agent-driven).** For unattended / agent use, the `lectern` CLI runs the same
pipeline to a `.pptx` without the web UI (install: `uv pip install -e apps/cli`):

```bash
lectern build <handoff-dir|pdf> --out deck.pptx            # full run; auto-approves the outline
lectern outline <handoff-dir|pdf> --out outline.json       # stop at the outline (optional review gate)
lectern build --from-outline outline.json --out deck.pptx  # resume from a reviewed outline
```

`build` is the one-shot path (auto-approves the outline gate) so an agent can go from a
Scriptorium `handoff` package straight to a deck; the `outline` → `--from-outline` pair makes
the outline review an optional file-contract step a human or agent can approve. It reuses the
same LangGraph graph + compiler as the API (no separate pipeline).

Configuration is via environment variables (see [`.env.example`](.env.example) for the full annotated
list). The essentials:

| Variable | Purpose |
|---|---|
| `ASA_LLM_PROVIDER` | `openai` \| `deepseek` \| `anthropic` |
| `ASA_<PROVIDER>_API_KEY` / `_BASE_URL` / `_MODEL` | per-provider key, private gateway URL, model override |
| `MINERU_API_KEY` | MinerU cloud parser (optional); without it, falls back to pdfplumber |
| `ASA_PDF_PARSER` | `auto` \| `mineru` \| `pdfplumber` \| `docling` |
| `ASA_STYLE` | `academic` (default) \| `modern_teal` |
| `ASA_VLM_CRITIC` / `ASA_VLM_MODEL` | opt-in post-render visual critique |
| `ASA_HOST` / `ASA_PORT` / `ASA_CORS_ORIGINS` / `ASA_OUT_DIR` | service host / port / CORS / output dir |

## Project Structure

```
packages/
  core/ir            # asa-slide-ir: the Slide-IR contract (Pydantic) — the single architectural invariant
  core/compiler      # asa-pptx-compiler: deterministic IR → native python-pptx (blocks, layout, diagrams, style, canvas)
  core/formula       # asa-formula: tiered formula rendering (matplotlib / MathJax sidecar / OMML) + icons
  ingestion          # asa-ingestion: parser cascade, cache, figure/panel handling, supplementary data
  agents             # asa-agents: outline + two-stage planners, deterministic critic, LangGraph orchestration
  providers          # asa-providers: LLM adapters (OpenAI-compatible, Anthropic) + named profiles
  vendor/svg2pptx    # asa-svg2pptx: vendored MIT SVG→DrawingML engine (see its README for provenance)
apps/
  api                # asa-api: FastAPI service (SSE, upload, approve, download, durable resume)
  cli                # asa-cli: headless `lectern` CLI (handoff → .pptx; optional outline file-contract gate)
  web                # asa-web: React + Vite + Tailwind export-first UI
docs/SPEC.md         # architecture constitution (living document + changelog)
openspec/            # spec-driven development: specs/ (live) + changes/archive/ (history)
templates/           # style/template assets
start-dev.bat        # one-click Windows dev launcher
```

## Status

Active. SPEC version **v0.5.5**; workspace packages at `0.1.0` (web UI `0.2.0`). Spec-driven via
[OpenSpec](https://github.com/Fission-AI/OpenSpec) — every capability starts as a reviewed change
proposal, is implemented, then archived into the live spec + changelog. Run the tests from the repo root
with `python -m pytest -q` (276 tests; 275 passing, 1 skipped). [`docs/SPEC.md`](docs/SPEC.md) is the
authoritative architecture constitution.

## License

**Apache-2.0** — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

The core (Slide-IR, agents, deterministic compiler) is a clean-room, independent implementation with no
AGPL/GPL code. Two components under `packages/vendor/svg2pptx` and
`packages/agents/asa_agents/canvas_exemplars` are vendored **exclusively from the MIT-licensed snapshot**
of `CRui5in/paper-ppt-agent` at commit `6f679fc` (2026-05-15, before it relicensed to AGPL); full
provenance is in `packages/vendor/svg2pptx/README.md`. Heavy tools are used at arms length (MinerU cloud
API, MathJax Node subprocess, optional Docling plugin).
