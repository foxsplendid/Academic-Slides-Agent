# Academic-Slides-Agent

> Turn hard-science papers (PDF + supplementary data) into **rigorous, native-editable `.pptx`**
> for academic group meetings (组会) and conference talks.

Unlike business-deck generators (Gamma, Tome), this tool targets the "hard science" bottlenecks:
heavy LaTeX math & chemistry, high-density experimental tables, real figures from the paper, strict
academic narrative, and unpublished-data privacy (bring-your-own model / self-hosted).

**Status:** working full-stack MVP. The pipeline runs end-to-end on real papers — MinerU parse →
two-stage planning + deterministic critic → human approval → native `.pptx` — verified with real
models (DeepSeek) and real geoscience/ML papers. 13 capabilities, ~142 tests, SPEC `v0.1.25`.
See [`docs/SPEC.md`](docs/SPEC.md) — the authoritative architecture constitution.

## Core idea (one line)

The LLM only ever emits a Pydantic-validated **Slide-IR** (structured JSON); a deterministic, AI-free
**compiler** renders it into native `python-pptx` objects. Orchestrated by **LangGraph** (human
Hard-Stop + streaming + resume). The frontend is **export-first** (no in-browser editor).

```
papers + ─▶ Ingestion ─▶ Evidence ─▶ Agents (LangGraph) ─▶ Slide-IR ─▶ Compiler ─▶ native
attachments   cascade      Pool       skeleton→expand→critic    (JSON)    (no AI)      .pptx
              + cache    (provenance)   ▲ human approval (Hard-Stop)   ▲ native tables/charts/
                                                                         diagrams/formulas/figures
```

**Why LLM-locked-to-IR?** The model is bad at geometry, so we never let it write coordinates, SVG, or
pptx. It supplies *semantics*; a deterministic engine computes the layout. This kills the dominant
failure mode (coordinate/overflow hallucination) and needs no vision-model repair loop.

## What it does

**Ingestion** — multi-file input (PDF + Excel/CSV/zip/images). Quality-gated parser cascade:
**MinerU** cloud API (high-fidelity text/formulas/tables/figures) → **Docling** (MIT, optional) →
**pdfplumber** (always-available fallback). Content-addressed parse cache; per-run isolation; optional
composite-figure panel splitting (`ASA_SPLIT_FIGURES`).

**Planning** — two-stage detailed planner (skeleton → per-slide focused expansion, each slide sees its
own evidence at full resolution), expanded in parallel. Chinese 组会 narrative with per-slide speaker
notes, an interpretation (`→`) bullet per slide, terminology kept verbatim, and figures grounded to
real Evidence-Pool asset ids (no hallucinated references). Deterministic dedup of near-duplicate
slides; IR-boundary retry heals malformed model output.

**Critic + human gate** — a deterministic, AI-free critic flags empty/overflowing slides, dangling
figure references, broken diagram edges, layout misselection, and near-duplicate titles; findings are
fed back for a bounded repair loop. A LangGraph `interrupt()` Hard-Stop lets a human approve the
outline before compilation.

**Compiler (native, fully editable)** — Slide-IR → native python-pptx:
- **Bullets / tables** with CJK-aware fonts and `**…**` red-bold emphasis
- **Charts** (`bar`/`line`/`scatter`/`pie`) → native, double-click-editable PowerPoint charts
- **Diagrams** (`flow`/`tree`/`cycle`/`comparison`/`pyramid`/`timeline`) — the LLM gives semantic
  nodes + edges (no coordinates); a deterministic layout engine emits native shapes + connectors
- **Figures** placed with aspect-preserving fit; figure/text height balanced so co-located bullets
  stay readable
- **Formulas** — tiered image rendering (matplotlib → MathJax+mhchem Node sidecar for chemistry /
  matrices), plus an experimental native-editable **OMML** tier (`ASA_NATIVE_FORMULA`, opt-in)
- **Style profiles** — design tokens (fonts/sizes/colors/emphasis) applied by the compiler;
  `ACADEMIC` (default) and `MODERN_TEAL`, swappable via `ASA_STYLE`

**Delivery** — FastAPI service (SSE streaming, upload, CORS) + a React export-first web UI
(upload → live progress → outline approval → download).

## Quickstart

```bash
# editable install of the workspace packages
pip install -e packages/core/ir -e packages/core/compiler -e packages/core/formula \
            -e packages/ingestion -e packages/agents \
            -e "packages/providers[openai]" -e apps/api      # or providers[anthropic]

# pick a provider (OpenAI-compatible: openai / deepseek, or anthropic)
export ASA_LLM_PROVIDER=deepseek
export ASA_DEEPSEEK_API_KEY=sk-...
# export ASA_OPENAI_BASE_URL=http://localhost:11434/v1      # or a local Ollama / vLLM (no key)

python -m asa_api                                            # serves on 127.0.0.1:8000
```

Drive it: `POST /jobs` or `POST /jobs/upload` (ingest inputs) → `GET /jobs/{id}/stream` (SSE) →
review the outline → `POST /jobs/{id}/approve` → `GET /jobs/{id}/download`.

The web UI lives in `apps/web` (`npm install && npm run dev`).

## Configuration

| Variable | Purpose |
|---|---|
| `ASA_LLM_PROVIDER` | `openai` \| `deepseek` \| `anthropic` (default `openai`) |
| `ASA_<NAME>_API_KEY` / `_BASE_URL` / `_MODEL` | per-profile key, private gateway URL, model override |
| `ASA_PDF_PARSER` | `auto` \| `mineru` \| `pdfplumber` (cascade entry point) |
| `MINERU_API_KEY` | MinerU cloud parser (arms-length HTTP; license-clean) |
| `ASA_STYLE` | `academic` (default) \| `modern_teal` |
| `ASA_EXPAND_WORKERS` | per-slide expansion concurrency (default 6) |
| `ASA_MAX_TOKENS` | optional output-token cap (latency) |
| `ASA_SPLIT_FIGURES` | opt-in composite-figure panel splitting |
| `ASA_NATIVE_FORMULA` | opt-in experimental native-editable OMML formulas |
| `ASA_DEBUG_TIMING` | emit a generation timing/concurrency probe |
| `ASA_HOST` / `ASA_PORT` / `ASA_CORS_ORIGINS` / `ASA_OUT_DIR` | service host/port/CORS/output dir |

Secrets belong only in a local, gitignored `.env` — never committed.

## Project structure

```
packages/
  core/ir/slide_ir          # the Slide-IR contract (Pydantic) — the single architectural invariant
  core/compiler/pptx_compiler# deterministic IR → native python-pptx (blocks, diagrams, style, charts)
  core/formula/formula_render# tiered formula rendering (matplotlib / MathJax sidecar / OMML)
  ingestion                 # parser cascade, cache, figures, panel split, supplementary data
  agents/asa_agents         # outline + two-stage deepen planners, critic, LangGraph orchestration
  providers/asa_providers   # LLM adapters (OpenAI-compatible, Anthropic) + named profiles
apps/
  api/asa_api               # FastAPI service (SSE, upload, approve, download)
  web                       # React export-first UI
docs/SPEC.md                # architecture constitution (living document + changelog)
openspec/                   # spec-driven development: specs/ (live) + changes/archive/ (history)
```

## Development

Spec-driven via [OpenSpec](https://github.com/Fission-AI/OpenSpec): every capability starts as a
reviewed change proposal, is implemented, then archived into the live spec + changelog.

```
propose  →  human review (the Hard-Stop of the dev process)  →  apply  →  archive
```

Run the tests: `python -m pytest -q` (from the repo root, with the editable installs above).

## License

**Apache-2.0** (see [`LICENSE`](LICENSE), [`NOTICE`](NOTICE)). Clean-room design — **no AGPL/GPL
code**; heavy tools are used at arms length (MinerU cloud API, MathJax Node subprocess, optional
Docling plugin). Inspired by MIT projects only (ppt-master, Auto-Slides, markitdown). This keeps an
open-core + closed-source SaaS path open.

## Roadmap

Position-/label-aware figure↔caption alignment; chart/diagram coverage nudges; native OMML coverage
(chemistry, matrices) verified in PowerPoint; VLM aesthetic critic; master-based template marketplace;
SaaS-ization (multi-tenant, CI license gate, CLA).
