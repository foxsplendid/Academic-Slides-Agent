# Academic-Slides-Agent — Architecture Specification (Constitution)

| | |
|---|---|
| **Status** | Living document — authoritative technical constraints |
| **Version** | 0.2.1 |
| **Last updated** | 2026-06-03 |
| **License** | Apache-2.0 |

> **Maintenance rule (binding).** This document is the single source of truth for
> architecture invariants. **Any change that alters an invariant MUST update this file in
> the same change and add a Changelog entry (§11).** Feature-level evolution happens through
> OpenSpec change proposals (`openspec/changes/*`); this SPEC holds only the *stable* spine.

---

## 1. Purpose & Non-goals

**Purpose.** Automatically transform hard-science papers (PDF / LaTeX source) **and their
supplementary data** (Excel/CSV/zip/PDF attachments) into **rigorous, native-editable
`.pptx`** decks for academic group meetings (组会) and conference talks.

**Differentiators (vs Gamma / Tome / generic generators):**
- Rigorous academic logic (Abstract → Methodology → Experiments/Data → Discussion → Conclusion); no fluff/hallucination.
- Faithful heavy math & chemistry (isotopes `^{143}Nd/^{144}Nd`, mineral formulae, DL losses).
- High-density experimental tables as **native editable PPT tables**, not images.
- Mapping into **fixed institutional/lab templates**.
- **Privacy**: robust local / self-hosted deployment for unpublished data.

**Non-goals (v1).**
- Not a business/marketing deck designer (no flashy auto-layout themes).
- Not an in-browser WYSIWYG editor (export-first; edit in real PowerPoint/WPS).
- Not native-editable equations in v1 (OMML is v2; v1 ships vector-image formulas).
- Not a general PDF table-reconstruction engine (PDF tables are best-effort).

---

## 2. License & Legal Constraints  ⚠️ (hard gate)

The project is **Apache-2.0** and must remain free of copyleft contamination so it can be
**open-core + closed-source SaaS** later.

**Dependency license policy.**

| Verdict | Examples | Rule |
|---|---|---|
| ✅ Allowed | MIT, BSD, Apache-2.0, ISC, MPL-2.0 (file-level) | Use freely; record in `NOTICE` |
| ⚠️ Review first | MinerU custom license (Apache-based + extra terms), LGPL | Read terms; isolate behind a boundary |
| ❌ **Forbidden** | **AGPL / GPL** of any kind | **CI must fail the build** |

**Named forbidden dependencies (do not introduce):**
- **PPTist** (AGPL) — this is *why* `paper-ppt-agent` is forced AGPL; never bundle it.
- **PyMuPDF / `fitz`** (AGPL) — use **`pypdfium2`** or **`pdfplumber`** instead.

**Clean-room policy.** Design is informed only by **ideas/requirements** (not copyrightable)
and by **MIT-licensed** references (ppt-master, Auto-Slides, markitdown). We **never** copy
code, file structure, or copyrighted expression from AGPL projects (`paper-ppt-agent`,
PPTist). Lessons distilled from prior AGPL work are written here as first-principles
requirements and re-implemented from scratch (e.g. via LangGraph natives).

**Hygiene to implement:** CLA for contributors; CI license-scan gate (fail on AGPL/GPL);
`NOTICE` lists all third-party attributions.

---

## 3. Architecture Overview

```
                 ┌───────────────────────── Evidence Pool ─────────────────────────┐
  inputs ─▶ Ingestion ─▶  typed assets {section_text | table | figure | dataset},  │
 (PDF/TeX +              each with provenance {source, page/section}                │
  xlsx/csv/zip)          └──────────────────────────┬───────────────────────────────┘
                                                     ▼
                         Agents (LangGraph state machine)
                         abstract → outline ─[interrupt: human Hard-Stop]─▶ map → compile
                                                                              │
                                            critic ◀──(conditional, max_retry)┘
                                                     ▼
                              Slide-IR (validated JSON)  ──▶  Compiler (deterministic, AI-free)
                                                                     │
                                                                     ▼
                                                          native .pptx (editable shapes/tables)
```

### 3.1 The one non-negotiable principle: **LLM output is LOCKED to Slide-IR**

The LLM is **only** permitted to emit a Pydantic-validated **Slide-IR** (structured JSON over
a closed vocabulary). It **never** emits SVG, code, or `.pptx`. A separate **deterministic,
AI-free compiler** turns IR into native `python-pptx` objects.

| Why this matters | Consequence |
|---|---|
| Validatable | malformed IR is rejected by Pydantic before rendering |
| Reproducible | same IR → same `.pptx`, always; debuggable |
| Template-decoupled | swap templates / restyle without re-running the LLM |
| Human-in-the-loop | user edits *structured IR*, not raw code; the Hard-Stop approves IR |
| Native & editable | compiler builds real tables/text → editable in PowerPoint |
| Safe | we never execute LLM-generated code |

Analogy: the LLM is the **screenwriter** (writes the script = IR); the compiler is the
**camera/director** (renders the film = pptx). The screenwriter never operates the camera.

---

## 4. Core Data Contracts

These Pydantic models are the **shared contract** between agents, compiler, frontend, and
checkpoints. They live in `packages/core/ir/` and are the single source of truth (export to
TS types for the frontend).

### 4.1 Slide-IR (LLM-produced, template-agnostic, user-approved)

```python
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field

class FormulaBlock(BaseModel):
    type: Literal["formula"] = "formula"
    latex: str
    render_tier: Literal["auto", "omml", "svg", "png"] = "auto"  # v1 resolves to svg
    rendered_ref: Optional[str] = None        # asset id/path filled by compiler

class TableBlock(BaseModel):
    type: Literal["table"] = "table"
    columns: list[str]
    rows: list[list[str]]
    caption: Optional[str] = None
    highlight: Optional[dict] = None          # e.g. {"col": 2}
    needs_human_check: bool = True            # PDF-extracted tables default to review

class BulletBlock(BaseModel):
    type: Literal["bullets"] = "bullets"
    items: list[str]

class FigureBlock(BaseModel):
    type: Literal["figure"] = "figure"
    asset_id: str                             # references an Evidence Pool figure
    caption: Optional[str] = None

class ChartBlock(BaseModel):                  # native, editable PowerPoint chart
    type: Literal["chart"] = "chart"
    chart_type: Literal["bar","line","scatter","pie"] = "bar"
    categories: list[str] = []
    series: list[ChartSeries]                 # {name, values, x?}  (data must come from evidence)
    title: Optional[str] = None

class DiagramBlock(BaseModel):                 # SEMANTIC logic diagram (NO coordinates)
    type: Literal["diagram"] = "diagram"
    diagram_type: Literal["flow","tree","cycle","comparison","pyramid","timeline"] = "flow"
    nodes: list[DiagramNode]                   # {id, label}
    edges: list[DiagramEdge] = []              # {source, target, label?} (from the paper)
    title: Optional[str] = None

Block = Annotated[
    FormulaBlock | TableBlock | BulletBlock | FigureBlock | ChartBlock | DiagramBlock,
    Field(discriminator="type"),
]

class SlideIR(BaseModel):
    slide_id: str
    layout_type: str          # enum: title|section|formula_banner|bullet_evidence|
                              #       two_column_table|figure_caption|...
    title: str
    blocks: list[Block] = []
    speaker_notes: str = ""
    provenance: dict = Field(default_factory=dict)   # {"source_section":"4.2","source_page":7}
```

### 4.2 Template Manifest (describes a `.pptx` master, content-agnostic)

```jsonc
{
  "template_id": "univ-blue-white",
  "layouts": [
    { "layout_name": "ContentTwoCol",
      "capability": ["title", "body_left", "body_right"],   // signature for the Mapper
      "placeholders": [
        {"name":"title","idx":0,"box":[0.5,0.4,9,1.0],"font":{"family":"Arial","max_pt":32}},
        {"name":"body_left","idx":1,"box":[0.5,1.6,4.3,5.0],"overflow":"shrink_then_spill"},
        {"name":"body_right","idx":2,"box":[5.2,1.6,4.3,5.0]}
      ] } ],
  "theme": {"primary":"#003A70","accent":"#0077B6"}
}
```

Tokenize an arbitrary uploaded `.pptx` with `python-pptx`: enumerate `slide_layouts` +
placeholder `idx/type/position/size/font` → emit a Manifest draft → one manual review → store.

### 4.3 Evidence Pool (normalized inputs + provenance → anti-hallucination)

All inputs (main paper + every attachment) normalize to one typed pool. Agents may only draw
from it; **every IR block carries `provenance` back to a pool asset.**

```python
class EvidenceAsset(BaseModel):
    asset_id: str
    kind: Literal["section_text", "table", "figure", "dataset"]
    content_ref: str                          # text / df handle / file path
    source: str                               # "paper.pdf" | "supp_data.xlsx#Sheet1" | ...
    locator: dict = Field(default_factory=dict)  # {"page":7} | {"sheet":"S1"} | {"section":"4.2"}
```

### 4.4 GenerationState (LangGraph state → checkpoint + stream + Hard-Stop)

```python
from enum import Enum
class Phase(str, Enum):
    INGESTING="ingesting"; ABSTRACTING="abstracting"; OUTLINING="outlining"
    AWAIT_OUTLINE_APPROVAL="await_outline_approval"   # ← Hard-Stop落点
    MAPPING="mapping"; COMPILING="compiling"; CRITIQUING="critiquing"
    EXPORTING="exporting"; DONE="done"; ERROR="error"

class GenerationState(BaseModel):
    job_id: str
    phase: Phase = Phase.INGESTING
    source_kind: Literal["pdf","tex"] = "pdf"
    evidence: list[EvidenceAsset] = []
    outline: Optional[list[dict]] = None          # tree, shown to user for approval
    user_approved_outline: bool = False           # set True on resume after interrupt
    user_outline_edits: Optional[list[dict]] = None
    slides: list[SlideIR] = []
    template_id: Optional[str] = None
    critic_findings: list[str] = []
    retry_count: int = 0
    max_retries: int = 2
    error: Optional[str] = None
```

---

## 5. Multi-Agent Orchestration (LangGraph)

**Why LangGraph:** native `interrupt()` (human Hard-Stop), checkpointer (resume/persist),
`astream`/`astream_events` (streaming) — exactly the three hard requirements. `core/` stays
framework-agnostic; only `packages/agents/` imports LangGraph.

**Graph:**
```
ingest → abstract → outline ─▶[interrupt: approve/edit outline]─▶ map → compile
                                                                       │
                                       ┌──── critic ◀──────────────────┘
                                       ▼ conditional edge (retry_count < max_retries)
                                {ok → export} / {fail → map}
                  └─▶[optional interrupt: preview approval]─▶ export(.pptx)
```

**Requirements distilled from prior work (first-principles, re-implemented via LangGraph):**
- **R1 Streaming.** Long generations must stream tokens/logs so proxies don't read-timeout
  (e.g. Cloudflare 524). Use `astream_events`; bridge to frontend via SSE/WebSocket.
- **R2 Resumable.** Run state must be checkpointed so a mid-run failure stays resumable.
  Use LangGraph checkpointer (Sqlite dev / Postgres prod) — **no bespoke session files**.
- **R3 Explicit resume entry.** There must be an API entry that re-enters a failed/paused
  run from its last checkpoint (don't strand persisted state with no consumer).
- **R4 Hard-Stop.** Pause at `AWAIT_OUTLINE_APPROVAL` via `interrupt()`; the user edits the
  outline; resume continues from the checkpoint.

---

## 6. Subsystem Specs

### 6.1 Ingestion → Evidence Pool
- **Priority: structured supplementary data.** `.xlsx/.csv` → DataFrame → `TableBlock`
  (lossless) via `pandas` (BSD) / `openpyxl` (MIT). This is where dense data lives and it is easy.
- **Archives:** unpack `.zip`, route by extension (xlsx/csv→table; pdf→text/figure; png→figure).
- **Main doc:** prefer **LaTeX source** (`\begin{table}` parses cleanly); else PDF→Markdown via
  `markitdown` (MIT).
- **PDF tables (best-effort only):** `pdfplumber` (MIT) for ruled tables; low-quality tables
  (no data rows / <2 cols / mostly auto-named headers) are dropped. Two-column pages are
  extracted column-by-column (gutter crop) to preserve reading order.
- **Quality-gated parser cascade (implemented).** PDFs go through ordered backends and **descend on
  poor output, not only on exceptions** (`assess_quality` scores text/pages/figures/tables):
  **MinerU** cloud API (Tier-1, `mineru.net/api/v4`, clean reading-order text + LaTeX + HTML tables +
  precise figure crops) → **Docling** (MIT, Tier-2, optional plugin, used only if installed) →
  **pdfplumber** (MIT, Tier-3, always available). All license-clean (arms-length API / MIT / MIT);
  **AGPL PyMuPDF and GPL Marker are forbidden.** `ASA_PDF_PARSER=auto|mineru|docling|pdfplumber`
  forces a single backend. Thin/scanned parses raise `IngestResult.warnings`, surfaced to the user
  pre-generation.
- **PDF figures (pdfplumber fallback):** hard-science figures are usually *vector*, so we **render**
  caption-anchored regions (`Fig. N` band) with `pypdfium2` → PNG → `figure` Evidence assets
  (`ingestion/figures.py`). The compiler resolves a figure block's `asset_id` to the rendered PNG
  via an `asset_resolver`. Best-effort regions; panel-splitting is out of scope.
- **Forbidden:** PyMuPDF/fitz (AGPL). Use `pypdfium2` (PDFium = BSD) for any PDF rasterization.

### 6.2 Formula (`packages/core/formula/`)
- **v1 (shipped):** LaTeX → **high-DPI PNG** via matplotlib `mathtext` (pure-Python, in-process,
  BSD; privacy-friendly, embeds directly through python-pptx `add_picture`). Unparseable input
  returns `None` → compiler text fallback. Lives behind the injectable `FormulaRenderer` interface.
- **v1.5 (shipped): MathJax(+mhchem) Node sidecar.** `AutoFormulaRenderer` tiers per formula —
  simple math → matplotlib (fast, no Node); advanced (`\ce{}` chemistry, matrices, alignment) →
  **MathJax → SVG → resvg PNG** via an **arms-length Node subprocess** (`formula/node/sidecar.js`;
  MathJax Apache-2.0 + resvg MPL-2.0, neither linked). Optional: enabled only when Node + the sidecar
  `node_modules` are present (`npm install`); else falls back. Behind the same `FormulaRenderer`.
- **v2 (enhancement):** LaTeX → MathML → **OMML** (`MML2OMML.XSL` XSLT) → native editable
  PowerPoint equation; auto-fallback to image on low-confidence conversion.
- **Regression set:** isotopes, subscripts, fractions, Greek, sums, roots via matplotlib;
  `mhchem`/matrices now render via the MathJax tier (verified `\ce{2H2 + O2 -> 2H2O}`, `pmatrix`).

### 6.3 Tables (`packages/core/tables/`)
- Normalize extracted/structured data → `TableBlock`; preserve significant figures & alignment.
- Compiler builds **native `python-pptx` tables** (editable), not images.

### 6.4 Template Mapping (`packages/core/mapper/`)
- Match IR `layout_type` → template `layout_name` by **capability signature**; fill placeholders.
- Compiler enforces fit (measure → shrink → spill). Learn from ppt-master (MIT) "follow your
  own .pptx template".

### 6.5 Critic / Overflow / Overlap detection
- **v1 (implemented, deterministic & AI-free):** `critique_deck` (in `asa_agents/critic.py`)
  measures the **Slide-IR** — title/bullet/table sizes, layout↔block consistency, and dangling
  figure `asset_id`s — and returns findings. The graph runs it **before** the Hard-Stop and
  re-plans with the findings as feedback, bounded by `max_retries` (default 2); residual findings
  still reach the human. Thresholds are module constants (`MAX_BULLETS`, `MAX_TABLE_ROWS`, …).
- **Primary (auto-fit implemented):** the compiler estimates bullet line count for the region
  (CJK-aware display width) and **shrinks the font to a floor** so dense text doesn't overflow
  ("measure, then place", `blocks._fit_font`). Pagination/spill to a continuation slide is still future.
- **Secondary (final QA only, v2):** optional VLM Critic renders the slide to image, flags
  overflow/overlap, loops back. Do not rely on VLM alone.
- **Structural guard:** "template as constraint" — content only enters predefined boxes, so
  overlap is prevented by design.

---

## 7. Frontend Contract (v1 = export-first)

- **No in-browser WYSIWYG editor** (avoids AGPL PPTist; editing happens in real PowerPoint).
- Frontend does: ① **outline-tree approval** (the Hard-Stop UI) ② **read-only preview**
  (render IR to images/SVG) ③ stream logs/progress.
- If editing is later needed, build a **minimal** editor on **Fabric.js / Konva.js (MIT)** that
  edits Slide-IR — not a PPTist clone.

---

## 8. Non-functional Requirements
- **Privacy:** first-class **local / self-hosted** deployment; no data leaves the host unless a
  remote model is explicitly configured.
- **Streaming, Resumable, Reproducible** (see §5 R1–R4; §3.1).
- **Determinism:** the compiler is pure (IR in → pptx out), unit-testable without any LLM.

---

## 9. Commercialization & Open-Core Boundary

Apache-2.0 enables open-core + closed SaaS (the whole reason to escape AGPL).

| Layer | Contents | Form |
|---|---|---|
| **OSS core** | IR, compiler, formula/table libs, CLI, single-user self-host, basic templates | Apache-2.0 |
| **Commercial** | hosted SaaS, team collaboration, template marketplace / lab-template onboarding, SSO, batch API, audit | closed |

Privacy (self-host OSS) answers "why open source"; convenience (managed/private-cloud) monetizes.

---

## 10. MVP Roadmap (risk-first — hard & defensible before easy & commoditized)

1. **Deterministic compiler**: hand-written IR + one real university template → beautiful native
   `.pptx`, **no AI**. Proves the hardest "native-editable + template" claim first.
2. **Formula pipeline** (v1 SVG) + regression test set. The credibility-defining module.
3. **Table/attachment ingestion** (xlsx/csv/zip first; PDF best-effort) + HITL preview.
4. **Single-agent** outline → IR + the Hard-Stop approval loop.
5. **LangGraph multi-agent** + Critic + streaming UI.
6. Minimal editor / SaaS — last.

> Build order is deliberately the reverse of "agents-first" blueprints: agents are commoditized;
> the compiler/formula/table engine is the moat and the risk.

---

## 11. Changelog

| Date | Version | Change |
|---|---|---|
| 2026-06-03 | 0.1.0 | Initial constitution: Apache-2.0 clean-room; LLM-locked-to-IR; LangGraph; export-first v1; formula SVG-first; Evidence-Pool ingestion; license forbidden-list (PPTist/PyMuPDF). |
| 2026-06-03 | 0.1.1 | Formula v1 changed from MathJax→SVG to **matplotlib mathtext→PNG** (in-process, BSD, privacy-friendly, direct python-pptx embedding); MathJax/SVG deferred to v1.5 behind the same `FormulaRenderer` interface. |
| 2026-06-03 | 0.1.2 | Critic §6.5 v1 landed: **deterministic, AI-free `critique_deck`** measuring Slide-IR + a **bounded `plan↔critic` retry loop** (feedback to planner, `max_retries`) running before the Hard-Stop. VLM critic stays v2. |
| 2026-06-04 | 0.1.3 | Quality tuning on a real paper (MiMo): planner now outputs a **Chinese 组会 talk** (method-paper narrative, concise titles, per-slide interpretation, **speaker notes**, terms kept original, figures grounded in the Evidence Pool — no hallucinated refs); compiler renders **16:9 + CJK fonts + `**…**` red-bold emphasis**; ingestion gains **two-column-aware PDF text** + **junk-table filtering** + wider digest. Figure *extraction* still deferred. |
| 2026-06-04 | 0.1.4 | **Figure extraction (§6.1) landed**: caption-anchored region rendering via `pypdfium2` (BSD) → `figure` Evidence assets; compiler resolves figure `asset_id`→rendered PNG via `asset_resolver`; planner sees figure ids+captions. Verified on Zhang 2026 (Fig.1–3 rendered, embedded natively). Vector figures handled; panel-splitting/OCR out of scope. |
| 2026-06-04 | 0.1.5 | **Resilient IR boundary**: `build_outline` retries transient malformed LLM output (dropped char / wrong enum / stray fence) up to `max_attempts` with the validation error fed back, re-raising only after the budget. The boundary stays strict; distinct from the critic loop (which re-plans a *valid* deck for quality). |
| 2026-06-04 | 0.1.6 | **MinerU cloud-API PDF backend** (§6.1): high-fidelity parsing (clean reading-order text, LaTeX formulas, HTML tables, precise `chart` figure crops + captions) via `mineru.net/api/v4`, an arms-length service (license-clean). Selected by `MINERU_API_KEY`/`ASA_PDF_PARSER`, pdfplumber fallback. Verified on Zhang 2026: 55k clean chars + 4 figures vs pdfplumber's jumbled text + 3 heuristic crops. |
| 2026-06-04 | 0.1.7 | **Two-stage detailed deck** (PPTAgent-style, `asa_agents/deepen.py`): skeleton plan → per-slide focused expansion (each slide sees its own evidence at full resolution) → deeper content (~5.4 substantive bullets/slide + real speaker notes vs ~3 generic). Graph planner is now injectable (`build_graph(planner=…)`, default single-shot `build_outline`); the server wires `build_deck_detailed`. Verified on Zhang 2026 (MinerU evidence). |
| 2026-06-04 | 0.1.8 | **Figure layout**: weighted per-block regions (figure ≫ table > formula > bullets) + aspect-preserving, centered figure fit (contain) with a caption line, replacing equal slices + forced full-width. Verified: Zhang figures keep their 1.46/4.75/1.05 ratios, centered, no overflow. |
| 2026-06-04 | 0.1.9 | **Parallel generation + live progress**: two-stage builder expands slides concurrently (thread pool, serial fallback on failure) with a `progress` callback; the graph `plan` node forwards it via LangGraph's custom stream writer; the SSE endpoint streams `progress` events; the web UI shows a phase stepper + live N/total slide counter. Verified live on Zhang 2026: `skeleton→slide 1..10→critic→awaiting_approval`. |
| 2026-06-04 | 0.1.10 | **Data charts**: new `ChartBlock` (bar/line/scatter/pie) in the locked IR vocabulary → **native, editable** python-pptx charts (CategoryChartData / XyChartData). Planner emits charts **only from evidence data (no fabrication)**. Verified: two-stage emitted 2 bar charts from real SHAP values, compiled as native charts. |
| 2026-06-06 | 0.1.11 | **Supplementary inputs reach generation**: skeleton plans gain `table_refs`; per-slide expansion is fed the referenced tables' actual data (`serialize_table`, high row cap + remainder note), so supplementary Excel/CSV data drives charts/discussion. Zip ingestion forwards the workspace to members; upload returns per-type counts; the web picker is supplementary-aware. Verified: a synthetic supp `.xlsx` → faithful native bar chart of all 6 rows. |
| 2026-06-06 | 0.1.12 | **Parser resilience (§6.1)**: quality-gated cascade MinerU → Docling (MIT, optional) → pdfplumber that descends on thin/empty output (not only exceptions); `assess_quality` + `IngestResult.warnings` surfaced to the user pre-generation. Backups filtered from the user's tool comparison (keep MIT/Apache/arms-length; reject AGPL PyMuPDF / GPL Marker). Verified: cascade descends on a thin parse; happy path unchanged. |
| 2026-06-06 | 0.1.13 | **Parse cache + run isolation**: content-addressed parse cache (`ingestion/cache.py`, sha256+parser; figures persisted, refs rewritten) so re-uploading the same paper skips parsing (verified **6.9s → 0.01s**, ~1000×). Each run writes `runs/<job_id>/` with `out.pptx` + `deck.json` + human-readable `deck.md` for comparing agent modes; cache under `<out_dir>/papers/`. |
| 2026-06-06 | 0.1.14 | **Logic diagrams** (`DiagramBlock`): the LLM emits a **semantic** diagram (nodes+edges+type, **no coordinates**) and a **deterministic layout engine** (`pptx_compiler/diagram.py`, 6 types: flow/tree/cycle/comparison/pyramid/timeline) renders native rounded-rect nodes + arrow connectors — no coordinate hallucination, no VLM needed (contrast: SVG-coordinate agents need a geometry+VLM critic). Critic validates edge node-refs. Verified: planner emitted a 4-stage flow from a paper's method; 6 types render native shapes. |
| 2026-06-06 | 0.1.15 | **Overflow auto-fit (§6.5)**: the compiler estimates bullet line count (CJK-aware) for the region and **shrinks the font to a floor** so dense academic text doesn't overflow ("measure, then place"). Pagination/spill still future. |
| 2026-06-06 | 0.1.16 | **Enhancement batch 1**: critic's `two_column_table` accepts table/chart/diagram (no more chart/diagram false-flags); default checkpointer registers `slide_ir` types so resume is msgpack-warning-free **and** future-strict-safe (verified 0 warnings, resume intact); the per-slide "→ interpretation" bullet is now mandatory in the expand prompt. |
| 2026-06-06 | 0.1.17 | **Enhancement batch 2 — incremental critic retry**: on a retry the two-stage builder repairs **only the flagged slides** (focused fix-this-slide call, prior topic/evidence preserved) and keeps the rest verbatim — no skeleton call, no re-expanding good slides. Verified: a one-slide defect makes exactly one LLM call instead of N+1. |
| 2026-06-06 | 0.1.18 | **Enhancement batch 3 — formula v1.5 (§6.2)**: MathJax(+mhchem) Node sidecar → resvg PNG behind a tiered `AutoFormulaRenderer` (simple→matplotlib, advanced→MathJax). **Chemistry/matrices now render instead of falling back to text** (verified `\ce{2H2+O2->2H2O}`, `pmatrix`, εNd). Optional (Node + `npm install`); arms-length subprocess (Apache/MPL, no linking). |
| 2026-06-06 | 0.1.19 | **Template system v1 = style profiles**: the reference look is per-shape (not a master/theme), so a "template" is a `StyleProfile` of design tokens (fonts/sizes/colors/emphasis/diagram colors) the compiler applies. `ACADEMIC` (user-derived tokens) is default → output unchanged; `compile_deck(style=…)` / `ASA_STYLE` swap it (verified academic↔modern_teal change fonts/colors). Optional `.pptx` base template still supported for master-based themes. |
| 2026-06-06 | 0.1.21 | **Figure panel splitting (opt-in)**: `ingestion/panels.py split_composite` — Pillow-only (numpy-free), AI-free band X-Y-cut gutter detection with conservative over-segmentation gates; under `ASA_SPLIT_FIGURES` each panel becomes a sibling `figure` asset (whole figure kept), flowing end-to-end with zero downstream changes. Verified 2×2→4 / 1×3→3; single/small don't split. |
| 2026-06-10 | 0.2.1 | **Content blocks + quality loop** (Path-A steps ④⑤): nested bullets (real buChar + hanging indent), `CalloutBlock` (tinted takeaway card, may replace the "→" bullet), `StatBlock` (1-4 big-number cards); **deterministic geometry lint** (`lint_compiled_deck`: font-floor cramming, tiny figures on figure-led layouts, shape overlap — exact, free, always on) + **opt-in VLM visual critic** (`ASA_VLM_CRITIC`; soffice→pypdfium2 render, PowerPoint COM dev fallback; CLOSED defect taxonomy → IR-level suggestions; fails open). Critic node runs the staged loop cheapest-first; findings join the bounded repair loop. |
| 2026-06-10 | 0.2.0 | **Layout v2 + Theme v1 + Data graphics v1** (research-driven quality wave; diagnosis: the gap was the 2-mold compiler, not the IR): multi-region layout templates (`figure_caption`=图右文左, new `figure_left`/`two_content`/`figure_grid`/`big_figure`, real `two_column_table`, strict composition matching + vertical-stack fallback); token-styled native charts (palette/axis fonts/data labels/bottom legend/gap 60) + tables (header fill, zebra banding, `highlight` implemented); deck chrome (accent rule, page numbers, cover/section rules); planner gets the 10-layout vocabulary; critic checks figure-led layouts. 19 new tests; verified by real-deck recompile. Strategy: Path A (evolve IR) confirmed; blind-comparison decision gate vs paper-ppt-agent before any Path-B escape hatch. |
| 2026-06-08 | 0.1.25 | **Remove MiMo profile + figure/text layout balance**: dropped the `mimo` built-in profile (key dead; supported profiles now `openai`/`deepseek` + `anthropic`); env-override example retargeted to `deepseek`. Compiler: figure-heavy slides cap the figure's vertical share so co-located bullets keep a readable minimum height. |
| 2026-06-08 | 0.1.24 | **Native-editable formulas (experimental, opt-in)**: clean-room `latex_to_omml` (LaTeX→OMML common subset, **no proprietary MML2OMML.XSL**; conservative — unsupported→None→image fallback); `AutoFormulaRenderer.to_omml` gated by `ASA_NATIVE_FORMULA` (default off); compiler embeds editable equation in `mc:AlternateContent` with LaTeX-text `mc:Fallback` (never blank/corrupt). Full OMML coverage (chemistry/matrices) + real-PowerPoint render verification deferred to v2 (arms-length Pandoc/texmath). |
| 2026-06-08 | 0.1.23 | **Dedup + layout fix**: deterministic `_dedup_plans` (difflib title+focus, CJK-safe, ratio ≥0.86) drops near-duplicate skeleton slides pre-expansion (critic can repair but never delete); `_fix_structural_layout` relayouts `section`/`title` dividers carrying content to `bullet_evidence`; SKELETON/EXPAND prompt rules (anti-redundancy + divider semantics); critic flags divider-with-content (repair-routable) and near-duplicate titles (human-facing, NOT repair-routable). |
| 2026-06-08 | 0.1.22 | **Generation speed (depth-safe)**: diagnosed 358s ≈ 13 calls × ~27.5s = serial gateway. Concise output ceilings in `EXPAND_SYSTEM` (notes 3–4 句, one-sentence bullets) = guaranteed per-call decode win; optional `max_tokens` (`ASA_MAX_TOKENS`, default unset); tunable `ASA_EXPAND_WORKERS` (was hard-coded 6); `ASA_DEBUG_TIMING` concurrency probe (wall vs sum); adaptive evidence cap (6000 for figure/table slides, 3800 for plain bullets). |
| 2026-06-06 | 0.1.20 | **Title color + scaffold profile**: `StyleProfile.title_rgb` (optional, applied to titles; `ACADEMIC` unchanged) + a `pptagent_academic` profile from PPT-Agent's `academic_defense` design *tokens* (dark-blue titles, dark-red emphasis, blue accents, 微软雅黑/Arial) — a **temporary scaffold** to be replaced by a user-derived profile. |
