## Why

Tested on a real paper (Zhang et al. 2026, machine-learning reconstruction of atmospheric O₂) with
MiMo and compared against a human-made 组会 deck for the *same* paper. The generated deck was
accurate in content but weak as a talk: English (audience is a Chinese 组会), a generic
Significance→Method→Conclusion skeleton, no speaker notes, a 127-char title dumped verbatim,
**hallucinated figure references** (`Fig. 1`/`Fig. 2` with no real assets), junk pdfplumber tables,
and a plain 4:3 look. This change tunes three layers so the output reads and looks like a research
group-meeting talk.

## What Changes

- **Outline agent (content):** rewrite the planner prompt to produce a Chinese 组会 talk with a
  method-paper narrative (科学问题→背景→数据/方法→结果/验证→讨论/机制→创新/展望), concise one-line
  titles, a per-slide interpretation ("→ 说明…"), and oral **speaker notes**. Technical terms,
  symbols, method names and citations stay in their original form. Figures may be referenced **only**
  by asset_ids that actually exist in the Evidence Pool; otherwise the figure is described as text (no
  hallucinated `figure` block). One key term/number per bullet may be wrapped in `**…**` for emphasis.
- **Compiler (look):** fresh decks render **16:9**; CJK-aware fonts (黑体 East-Asian + Times New Roman
  Latin); title 28pt bold / body 16pt / caption 12pt; `**…**` spans render **bold red** (FF0000),
  matching the reference deck's emphasis convention.
- **Ingestion (clean inputs):** two-column-aware PDF text extraction (crop by gutter so columns are
  no longer interleaved); drop low-quality pdfplumber tables (no data rows, <2 columns, or mostly
  auto-named `colN` headers); widen the evidence digest budget so the planner sees more of the paper.

## Capabilities

### Modified Capabilities
- `outline-agent`: Chinese 组会 narrative + speaker notes + concise titles + emphasis + figure
  grounding (no hallucinated asset_ids).
- `pptx-compiler`: 16:9, CJK fonts, sized type, and `**…**` red-bold emphasis runs.
- `ingestion`: column-aware PDF text + junk-table filtering + larger evidence budget.

## Non-goals

- Figure **extraction** from the PDF (the deck stays text-for-figures until that capability lands).
- A full template system / theme files; styling is in-code defaults for now.

## Impact

- `outline.py` (prompt + digest + figure-id passing), `pptx_compiler` (compiler.py + blocks.py),
  `ingestion/pdf.py` + `models.py`. No new dependencies, no IR schema change (`**…**` is a text
  convention; `speaker_notes` already exists on `SlideIR`). Verified on the real Zhang 2026 PDF.
