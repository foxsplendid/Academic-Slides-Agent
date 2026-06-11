# Academic-Slides-Agent — Architecture Specification (Constitution)

| | |
|---|---|
| **Status** | Living document — authoritative technical constraints |
| **Version** | 0.5.0 |
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
| 2026-06-12 | 0.5.0 | **信息设计组件波次**(对标对方 GSA 模板系统的最后失分项,全确定性):①**kicker 样式化横条**——内容页导读句从素文字升级为全宽色带(card_fill 底+4pt 强调左边+居中加深文字);②**分隔页本章预览**——section 页自动列出本章内容页标题(≤4 条,muted,从 deck 自身推导、零 IR/提示词改动),「低信息量结构页」批评失效;③**stat 统计芯片**——卡片顶部 3pt 强调色边。配 R6' 收尾:重复用图 critic、grow-to-fit、封面缩号。258 测试,R6' deck 重编译视觉验证通过。 |
| 2026-06-12 | 0.4.4 | **R6' 复验:回归修复完全生效(零缺图指控,13 图块全部正常)但未达收官判据**(偏好 1胜3负、Design −0.38;R5↔R6' 振荡表明当前处于胜负相当区间,run 间方差成为主导因素)。新发现修复:①critic **重复用图检查**(同图嵌两页=图文错配信号,R6' p10/p13,repair-routable);②bullets **grow-to-fit**(文本填充 <55% 区域时字号上浮至 +6pt,治下半页留白);③封面长标题自动缩字号(>18 字渐缩,防生硬断行)。256 测试。剩余 Design 失分主项=信息设计组件表现力(对方 GSA 模板系统),留待下波。 |
| 2026-06-12 | 0.4.3 | **R6 回归修复(判团裁定:R6 0/4 是渲染回归非设计问题——骨架一次劣化滚动没填 figure_ids+编造短 id,修复阶段拿不到图清单只能盲修,2 轮耗尽后 fail-open 空图 deck 流入盲测)**。三层加固:①**骨架计划验证**(_plan_errors/_sanitize_plans:编造 id 或图版式无有效图 → 一次带错重问 → 仍坏则确定性剥离+降级 bullet_evidence——「承诺了图却空页」失败类从此不可能);②**修复带图清单**(图相关 findings 时 _repair_slide 注入 figure_menu,修复从盲修变能修);③扩写不再信任回显 slide_id(plan 持有,修复 '<沿用>' 占位符串号)。255 测试。复验轮(同协议)进行中。 |
| 2026-06-12 | 0.4.2 | **R5 三项打磨**(判团点名,备战 R6):①长宽比自适应扩展——big_figure 方/高图(ar<1.35)自动改侧排(不再整宽带 letterbox)、全景图(ar>2.2)自动改全宽顶带+文下;②密集原图策略(提示词):图注/图例密集的原图优先 big_figure 放大或拆子图,勿塞半栏;图主导页 bullets ≤4 条且每条≤40字(图是主角,长解读进讲稿);③信息设计手法:方法对比/前人缺陷优先 table 对照表(✓/✗/数值),stat 支持「0.89 → 0.93」箭头形式。252 测试。 |
| 2026-06-12 | 0.4.1 | **盲测 R5:偏好首次反转 3我方/1平/0对方**(R1-R4 全 0 胜)!Design 从 R4 −1.25 翻正到 **+0.38**(3.63 vs 3.25,首次反超)、Content +0.50 领先、Coherence −0.13 基本打平。翻盘根因(四评委一致):我方嵌入**真实完整渲染的论文级图件、零损坏**,对方自建图表系统性损坏(SHAP 无轴/雷达无迹线/柱状叠压/卡片溢出)——**no-coordinates 论点五轮数据彻底验证**。R5 收尾修复:封面缺作者(模型漏填)→ 封面扩写强制纳入第 1 页证据+critic 强制封面副标题非空(可修复)。250 测试。剩余打磨:个别图仍偏小、截图图注偏小、版式偏单调。 |
| 2026-06-12 | 0.4.0 | **Theme v3 统一外壳(R4 裁决:Content 已平手 4.13,纯输机械一致性)**。盲测 R4:Design 差 1.25(最大)/Coherence 差 0.75/偏好 1平3负,四评委每轮同点:图小留白大、页脚章节错、脱模板页、封面缺作者。全确定性编译器修复:①**长宽比自适应图列**(_aspect_fraction:列宽≈长宽比×高,clamp 0.42-0.66,消除小图大留白);②**统一页脚**(每页含结构页:编号面包屑「NN · 章节」+页码,首章前回退 deck 标题)+**running head**(右上 deck 标题);③结构页(section/ending)不再脱壳、与内容页同款页脚;④封面副标题改作者·单位·年份;⑤骨架规则 section 紧贴本章内容(修页脚串号)、canvas 页加同款底部页脚。249 测试。 |
| 2026-06-12 | 0.3.4 | **图注匹配 + 一致性散点**:①ingestion 同页多面板**图注传播**(_propagate_panel_captions:同页恰一张带「FIGURE N」完整图注+其余为「(b)」式碎片→判定为同图子面板,完整图注+panel 序号+fig_no 传播到全部,缓存 v5)——根治多面板图被拆成独立资产后模型编造子图注;扩写新规子图注「只写画面可确认内容,不确定只留图号,严禁编造」;②ChartBlock.reference_line:预测-vs-参考一致性用**单 series 散点(x=参考,y=预测)+ 自动 1:1 对角线**(虚线灰),比两条并排折线直观;chart 选型提示对应更新。247 测试。 |
| 2026-06-12 | 0.3.3 | **叙事与内容打磨波次**:①前端 Lightbox 大图左右箭头/键盘切换(Approval+Result 共用);②图注注明原文图号(「图N | 描述」,子图「图N-子图i」);③**子图使用语义**(用户设计意图:拆图为横排同屏,非挑单张)——整图或同图多子图 figure_grid 横排,单子图仅限大幅机制图,小图禁单独成页;ingestion 记录像素尺寸(locator.px,缓存 v4),图清单标注尺寸与小图警示;④章节编号 chrome:section 分隔页大数字 01/02 + 页脚「02 · 章节名」编号面包屑;⑤结论式导读句 + 文献引用保留 (作者, 年份);CORS 放行任意 localhost 端口。245 测试。 |
| 2026-06-12 | 0.3.2 | **盲测 R3:Design 追平(差 0 vs R1 0.625/R2 0.75)**,8/8→12/12 偏好仍对方但归因已收敛至 Coherence(-1.0)/Content(-0.375)。R3 速修:canvas 禁工具痕迹(Source/Evidence 字样)+禁无证据数据点+学术观感统一;骨架"总结收口(≤1 总结页)/展望须来自论文/toc-章节一一对应";critic 新增 toc-section 一致性检查(全局发现→全量重规划)与 [建议] 前缀建议性发现(不消耗重试预算,after_critic 过滤)。243 测试。 |
| 2026-06-12 | 0.3.1 | **精品档转正 + 通用构图引擎**:premium 默认开启(骨架按页选 canvas/积木,积木为质量地板);canvas 确定性几何 lint(文本溢出/重叠估算,接入创作重试与 critic);12 个 MIT 构图范例 vendored+按页意图 few-shot 注入;**通用构图引擎替代枚举模板**(majors 侧排/网格、stat 顶带、callout 底带、双列表并排——"无模板匹配→纵向堆叠"失败类消除)。真模冒烟:范例引导下散点+对照表+诊断卡页,守卫与几何 lint 一次通过。241 测试。另修:拒绝反馈全量重规划、稀疏页 critic、grid 图数检查(0.3.0 后)。 |
| 2026-06-11 | 0.3.0 | **Path B 落地:VisualCanvas 精品档**(B-b/B-c)。CanvasBlock+canvas 版式:LLM 在受约束整页 SVG(viewBox 1280x720)上自由构图;三层防线=canvas guard(禁 script/foreignObject/动画/媒体/image/外链,白名单调色板与字体契约)→ vendored finalize 确定性修复 → svg2pptx 转**原生可编辑** DrawingML 注入包内(矢量+文本,rels 不动,全程 fail-open;lint 跳过 canvas 页)。生成侧:premium 选项→骨架可为最关键 2-3 页规划 canvas,CANVAS_SYSTEM 专用创作提示+守卫验证重试+降级 bullet 兜底;前端精品档开关。**架构原则更新:LLM-不写坐标 现在限定于快速档;精品档以 guard+确定性修复+可视 QA 换表达力,可编辑性硬约束不变。** 真模冒烟:DeepSeek 一次通过守卫,产出森林图对比+性能卡+迷你散点页,40 可编辑文本形状。234 测试。 |
| 2026-06-11 | 0.2.7 | **释放模型表达 + Path B-(a)**: 全管线约束审计(20 保护性保留/11 放开/10 软化/10 Path B 天花板)。页数与密度默认**模型自决**(auto 档,brief/normal/high 退为软目标);figure_ids 列表化(figure_grid 端到端可表达);图页版式不再强制 figure_caption;配额改指导(强调/图标/章节数/单调);证据可见度提升(digest 24k、扩写 6k/9k、图注 600);图标开放词汇(目录扫描 fail-open);critic 再校准(MAX_BULLETS 9/单调建议性/stat 上限改可修复);TOC 双栏;ASA_MINERU_LANG/ASA_TEMPERATURE。**B-(a) 完成**: MIT 快照 6f679fc 的 svg_to_pptx+finalize 已 vendor(packages/vendor/svg2pptx,NOTICE 署名,LGPL svglib 惰性隔离),真实 SVG→可编辑 PPTX 冒烟通过。 |
| 2026-06-11 | 0.2.6 | **Theme v2 + 盲测决策门两轮记录**: SlideIR.subtitle(封面元信息/内容页导读句/分隔页导语)+页脚章节导航+强制章节页;复测回归修复(内容页预算排除结构页/每章至少1图/bullets 适配 8% 安全边距/术语统一规则)。门记录:R1 Design 差 0.625,R2(Theme v2 后)0.75,两轮 8/8 评委偏好对方——**按预定阈值 Path B 触发**(对方持久优势=页内信息设计:卡片/引文/对照表;其自绘 SVG 图表大面积损坏反证我方 no-coordinates 路线)。 |
| 2026-06-10 | 0.2.5 | **P2: 图标体系 + 模板导入**: Tabler 图标(MIT 上游 npm)经 Node/resvg 边车染色出 PNG(`IconRenderer`+44 名**封闭白名单**,未知名静默跳过=宁缺勿滥);`CalloutBlock.icon`/`StatItem.icon` IR 字段+编译器注入式 `icon_resolver`+prompt 白名单策略(每页≤2)。模板导入:`POST /templates` 上传 .pptx → 确定性提取 theme(major 字体+accent1-6 调色盘)→ 注册自定义 StyleProfile(`base_template` 指向原文件→编译时**原生继承母版**),JSON 持久化+启动重水化,前端风格下拉+导入按钮。 |
| 2026-06-10 | 0.2.4 | **Durable resume(断点续跑)**: 任务执行与 SSE 连接解耦(后台线程+可重放事件日志+keepalive,掉线不再中止生成、重连重放);`durable_checkpointer`(SqliteSaver+slide-ir serde)+初始状态落盘——**重启后端任务可续**(实测:中断任务从检查点续跑→Hard-Stop→杀进程→重启→跨重启批准→下载);stream 端点阶梯语义(live attach→审批重放→断点续跑→done 重放→冷启动);异常以 error 事件带真因;修复加固(_REPAIR_SYSTEM 枚举块词汇/表 title→caption 规整/**修复耗尽保留原页 fail-open 到 Hard-Stop**);前端 followJob+自动重连+历史可点开续跑(running/interrupted 状态)。 |
| 2026-06-10 | 0.2.3 | **P1: structure pages + layout variety + detail levels + chart taxonomy** (paper-ppt-agent methodology wave): `toc`(数字章 agenda)/`ending` 版式 + cover→toc→sections→ending 叙事;骨架把版式分配当 deck 级设计决策(图左右交替/big_figure 放大关键图/禁 4+ 连续同版式)+ critic 确定性单调检查(>3 连续同版式可路由修复,分隔页重置);量化密度档位 `DETAIL_PROFILES`(brief/normal/high 页数+bullets+notes 配额)从上传表单经 options 贯通到双段 prompt,前端加详细程度选择;图表选型分类学(对比→bar/趋势→line/占比→pie/相关→scatter)。 |
| 2026-06-10 | 0.2.2 | **Web UI rewrite + visual approval** (modeled on paper-ppt-agent's UX, clean-room, MIT deps only, export-first preserved): 3-view app shell (Tailwind+lucide+zustand) — sidebar history (GET/DELETE /jobs + meta.json), Generate view (drag-drop + per-job options style/parser/split/VLM/OMML + staged progress), **visual approval** (POST /jobs/{id}/preview renders the in-flight deck via the visual-critic renderer chain → real slide thumbnails + lightbox; approve / reject-with-feedback), Result view (preview + download with disk fallback). Orchestration: approval node honors rejection (feedback→findings→replan→new Hard-Stop, resumed over SSE `?reject=1`); per-job style/options ride GenerationState. |
| 2026-06-10 | 0.2.1 | **Content blocks + quality loop** (Path-A steps ④⑤): nested bullets (real buChar + hanging indent), `CalloutBlock` (tinted takeaway card, may replace the "→" bullet), `StatBlock` (1-4 big-number cards); **deterministic geometry lint** (`lint_compiled_deck`: font-floor cramming, tiny figures on figure-led layouts, shape overlap — exact, free, always on) + **opt-in VLM visual critic** (`ASA_VLM_CRITIC`; soffice→pypdfium2 render, PowerPoint COM dev fallback; CLOSED defect taxonomy → IR-level suggestions; fails open). Critic node runs the staged loop cheapest-first; findings join the bounded repair loop. |
| 2026-06-10 | 0.2.0 | **Layout v2 + Theme v1 + Data graphics v1** (research-driven quality wave; diagnosis: the gap was the 2-mold compiler, not the IR): multi-region layout templates (`figure_caption`=图右文左, new `figure_left`/`two_content`/`figure_grid`/`big_figure`, real `two_column_table`, strict composition matching + vertical-stack fallback); token-styled native charts (palette/axis fonts/data labels/bottom legend/gap 60) + tables (header fill, zebra banding, `highlight` implemented); deck chrome (accent rule, page numbers, cover/section rules); planner gets the 10-layout vocabulary; critic checks figure-led layouts. 19 new tests; verified by real-deck recompile. Strategy: Path A (evolve IR) confirmed; blind-comparison decision gate vs paper-ppt-agent before any Path-B escape hatch. |
| 2026-06-08 | 0.1.25 | **Remove MiMo profile + figure/text layout balance**: dropped the `mimo` built-in profile (key dead; supported profiles now `openai`/`deepseek` + `anthropic`); env-override example retargeted to `deepseek`. Compiler: figure-heavy slides cap the figure's vertical share so co-located bullets keep a readable minimum height. |
| 2026-06-08 | 0.1.24 | **Native-editable formulas (experimental, opt-in)**: clean-room `latex_to_omml` (LaTeX→OMML common subset, **no proprietary MML2OMML.XSL**; conservative — unsupported→None→image fallback); `AutoFormulaRenderer.to_omml` gated by `ASA_NATIVE_FORMULA` (default off); compiler embeds editable equation in `mc:AlternateContent` with LaTeX-text `mc:Fallback` (never blank/corrupt). Full OMML coverage (chemistry/matrices) + real-PowerPoint render verification deferred to v2 (arms-length Pandoc/texmath). |
| 2026-06-08 | 0.1.23 | **Dedup + layout fix**: deterministic `_dedup_plans` (difflib title+focus, CJK-safe, ratio ≥0.86) drops near-duplicate skeleton slides pre-expansion (critic can repair but never delete); `_fix_structural_layout` relayouts `section`/`title` dividers carrying content to `bullet_evidence`; SKELETON/EXPAND prompt rules (anti-redundancy + divider semantics); critic flags divider-with-content (repair-routable) and near-duplicate titles (human-facing, NOT repair-routable). |
| 2026-06-08 | 0.1.22 | **Generation speed (depth-safe)**: diagnosed 358s ≈ 13 calls × ~27.5s = serial gateway. Concise output ceilings in `EXPAND_SYSTEM` (notes 3–4 句, one-sentence bullets) = guaranteed per-call decode win; optional `max_tokens` (`ASA_MAX_TOKENS`, default unset); tunable `ASA_EXPAND_WORKERS` (was hard-coded 6); `ASA_DEBUG_TIMING` concurrency probe (wall vs sum); adaptive evidence cap (6000 for figure/table slides, 3800 for plain bullets). |
| 2026-06-06 | 0.1.20 | **Title color + scaffold profile**: `StyleProfile.title_rgb` (optional, applied to titles; `ACADEMIC` unchanged) + a `pptagent_academic` profile from PPT-Agent's `academic_defense` design *tokens* (dark-blue titles, dark-red emphasis, blue accents, 微软雅黑/Arial) — a **temporary scaffold** to be replaced by a user-derived profile. |
