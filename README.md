# Academic-Slides-Agent

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-264_passing-brightgreen.svg)](#development)
[![Spec](https://img.shields.io/badge/SPEC-v0.5.3-informational.svg)](docs/SPEC.md)

**English** · [简体中文](README.zh-CN.md)

> Turn a hard-science paper (PDF + supplementary data) into a **rigorous, natively-editable `.pptx`**
> for academic group meetings (组会) and conference talks — in one upload.

Unlike business-deck generators (Gamma, Tome), Academic-Slides-Agent targets the *hard-science*
bottlenecks: heavy LaTeX math and chemistry, high-density experimental tables, **real figures lifted
from the paper**, a strict academic narrative, and bring-your-own-model privacy for unpublished data.
Every slide it produces is a **real PowerPoint object** — editable text, native tables, native
charts, vector shapes — never a screenshot.

---

## Why it's different

The single architectural rule: **the LLM only ever emits a Pydantic-validated `Slide-IR`** (structured
JSON over a closed vocabulary). A separate **deterministic, AI-free compiler** turns that IR into native
`python-pptx` objects. The model supplies *semantics*; a deterministic engine computes *geometry*.

| | Academic-Slides-Agent | LLM-writes-SVG/coordinates tools |
|---|---|---|
| Figures/charts | native, editable, never broken | frequently render empty / mislabelled / overlapping |
| Failure mode | rejected by schema before render | coordinate & overflow hallucination |
| Reproducible | same IR → same `.pptx`, always | stochastic per run |
| Editing | real PowerPoint shapes & tables | flattened vectors / images |

This "never let the model write coordinates" thesis was **validated empirically**: in a blind, same-paper,
same-renderer A/B evaluation against an AGPL agent-mode generator, judges independently and repeatedly
flagged the opponent's *self-drawn charts* as the recurring fatal defect (axis-less SHAP plots, empty
panels, overlapping labels), while this project's decks carried **zero broken figures**. Over six rounds,
preference moved from 0/4 to a 3/4 win once a uniform deterministic chrome closed the remaining
mechanical-consistency gap.

```
papers + ─▶ Ingestion ─▶ Evidence ─▶ Agents (LangGraph) ─▶ Slide-IR ─▶ Compiler ─▶ native
attachments   cascade      Pool       skeleton→expand→critic    (JSON)    (no AI)      .pptx
              + cache    (provenance)   ▲ human approval (Hard-Stop)   ▲ tables/charts/diagrams/
                                                                         formulas/figures/canvas
```

## What it does

**Ingestion** — multi-file input (PDF + Excel/CSV/zip/images), **or a Scriptorium `handoff/1.x` package**
(a directory with `meta.json` + one or more PDFs, staged by [Steward](https://github.com/scriptorium-suite/steward)
`pick`): single-paper or a multi-paper literature/experiment report, with title/authors/year/DOI injected
as provenance. Quality-gated parser cascade: **MinerU** cloud API (high-fidelity text/formulas/tables/figures)
→ **Docling** (MIT, optional) → **pdfplumber** (always-available local fallback). Content-addressed parse
cache; per-run isolation; composite-figure panel detection and same-page panel grouping so multi-panel
figures are never used as if they were the whole figure.

**Planning** — a two-stage planner (skeleton → per-slide focused expansion, each slide seeing its own
evidence at full resolution), expanded in parallel. Academic 组会 narrative with per-slide speaker notes,
an interpretation bullet per results page, terminology kept verbatim, citations preserved, and every
figure grounded to a real Evidence-Pool asset id — no hallucinated references. Page count and density are
**model-decided by default** (the paper drives the length); optional brief/normal/high presets remain.

**Critic + human gate** — a deterministic, AI-free critic flags empty/overflowing slides, dangling figure
references, broken diagram edges, layout misselection, near-duplicate titles, table-of-contents ↔ section
mismatches, duplicate figures and sparse pages; findings feed a bounded repair loop. A LangGraph
`interrupt()` **Hard-Stop** lets a human approve (or reject with feedback) the outline before compilation
— reject a specific page by number and only that page is regenerated.

**Compiler (native, fully editable)** — Slide-IR → native python-pptx:
- **Bullets / tables** with CJK-aware fonts and `**…**` emphasis
- **Charts** (`bar`/`line`/`scatter`/`pie`) → native, double-click-editable PowerPoint charts, incl. a
  predicted-vs-reference agreement scatter with an automatic 1:1 line
- **Diagrams** (`flow`/`tree`/`cycle`/`comparison`/`pyramid`/`timeline`) — the LLM gives semantic
  nodes + edges (no coordinates); a deterministic layout engine emits native shapes + connectors
- **Figures** placed by a general layout compositor that sizes columns to each figure's aspect ratio
  (no more "tiny image, big empty canvas")
- **Formulas** — tiered image rendering (matplotlib → MathJax + mhchem Node sidecar) plus an
  experimental native-editable **OMML** tier
- **Deck chrome** — numbered section dividers with chapter previews, a styled kicker takeaway band,
  uniform running header + numbered footer breadcrumb on every page, stat "chips"
- **Premium VisualCanvas tier** — for the most valuable result/mechanism pages the model may author a
  whole constrained-SVG page (free composition); a closed-ban guard + deterministic geometry lint +
  the vendored MIT SVG→DrawingML engine turn it into **editable vector + text** (never a screenshot),
  with automatic fallback to deterministic layouts on any failure

**Delivery** — FastAPI service (SSE streaming, durable background runs, resume) + a React export-first
web UI (upload → live progress → outline approval → download), with a full-screen slide viewer.

## Quickstart

**One-click (Windows):** double-click [`start-dev.bat`](start-dev.bat) — it checks `.venv`/npm, installs
frontend deps on first run, starts the backend (`:8000`) and the Vite dev server (`:5173`) in their own
windows (reusing any already running), and opens the browser.

**Manual setup:**

```bash
# 1) Python deps — editable install of the workspace packages (uv recommended; pip works too)
uv venv && . .venv/bin/activate          # or: python -m venv .venv && source .venv/bin/activate
uv pip install -e packages/core/ir -e packages/core/compiler -e packages/core/formula \
               -e packages/ingestion -e packages/agents -e packages/vendor/svg2pptx \
               -e "packages/providers[openai]" -e apps/api     # or providers[anthropic]

# 2) Configure — copy the template and fill in your own keys
cp .env.example .env        # then edit .env (it is gitignored — never commit real keys)

# 3) Run the API
python -m asa_api           # serves on http://127.0.0.1:8000

# 4) Run the web UI (separate terminal)
cd apps/web && npm install && npm run dev   # http://localhost:5173
```

Or drive the API directly: `POST /jobs/upload` (ingest inputs) → `GET /jobs/{id}/stream` (SSE) → review
the outline → `POST /jobs/{id}/approve` → `GET /jobs/{id}/download`.

## Configuration

All configuration is via environment variables (a local, gitignored `.env`). See
[`.env.example`](.env.example) for the full annotated list. The essentials:

| Variable | Purpose |
|---|---|
| `ASA_LLM_PROVIDER` | `openai` \| `deepseek` \| `anthropic` |
| `ASA_<PROVIDER>_API_KEY` / `_BASE_URL` / `_MODEL` | per-provider key, private gateway URL, model override |
| `MINERU_API_KEY` | MinerU cloud parser (optional; arms-length HTTP). Without it, falls back to pdfplumber |
| `ASA_PDF_PARSER` | `auto` \| `mineru` \| `pdfplumber` \| `docling` |
| `ASA_STYLE` | `academic` (default) \| `modern_teal` |
| `ASA_VLM_CRITIC` / `ASA_VLM_MODEL` | opt-in post-render visual critique |
| `ASA_HOST` / `ASA_PORT` / `ASA_CORS_ORIGINS` / `ASA_OUT_DIR` | service host / port / CORS / output dir |

> **Privacy:** secrets live only in your local `.env`. Point `ASA_OPENAI_BASE_URL` at a local Ollama/vLLM
> endpoint to keep unpublished data entirely on your own hardware.

## Project structure

```
packages/
  core/ir/slide_ir            # the Slide-IR contract (Pydantic) — the single architectural invariant
  core/compiler/pptx_compiler # deterministic IR → native python-pptx (blocks, layout, diagrams, style, canvas)
  core/formula/formula_render # tiered formula rendering (matplotlib / MathJax sidecar / OMML) + icons
  ingestion                   # parser cascade, cache, figure/panel handling, supplementary data
  agents/asa_agents           # outline + two-stage planners, deterministic critic, LangGraph orchestration
  providers/asa_providers     # LLM adapters (OpenAI-compatible, Anthropic) + named profiles
  vendor/svg2pptx             # vendored MIT SVG→DrawingML engine (see its README for provenance)
apps/
  api/asa_api                 # FastAPI service (SSE, upload, approve, download, durable resume)
  web                         # React export-first UI
docs/SPEC.md                  # architecture constitution (living document + changelog)
openspec/                     # spec-driven development: specs/ (live) + changes/archive/ (history)
```

## Development

Spec-driven via [OpenSpec](https://github.com/Fission-AI/OpenSpec): every capability starts as a reviewed
change proposal, is implemented, then archived into the live spec + changelog.

```
propose  →  human review (the Hard-Stop of the dev process)  →  apply  →  archive
```

Run the tests from the repo root: `python -m pytest -q` (264 passing).
[`docs/SPEC.md`](docs/SPEC.md) is the authoritative architecture constitution.

## License & attribution

**Apache-2.0** (see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE)).

The core (Slide-IR, agents, deterministic compiler) is a clean-room, independent implementation with **no
AGPL/GPL code**. Two components under `packages/vendor/svg2pptx` and `packages/agents/asa_agents/canvas_exemplars`
are vendored **exclusively from the MIT-licensed snapshot** of `CRui5in/paper-ppt-agent` at commit `6f679fc`
(2026-05-15, before it relicensed to AGPL); full provenance is in `packages/vendor/svg2pptx/README.md`.
Heavy tools are used at arms length (MinerU cloud API, MathJax Node subprocess, optional Docling plugin).
This keeps an open-core path open.

## Roadmap

Position/label-aware figure↔caption alignment; richer chart and diagram coverage; native OMML verified in
PowerPoint (chemistry, matrices); template marketplace via master inheritance; broader style profiles.
