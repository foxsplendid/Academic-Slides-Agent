"""Outline agent: Evidence Pool -> Slide-IR Deck, enforcing the IR boundary.

The LLM's output is parsed through ``from_llm_output``, so prose/code/HTML are rejected and never
reach the compiler ("LLM locked to IR", docs/SPEC.md §3.1).
"""

from __future__ import annotations

from slide_ir import Deck, EvidenceAsset, TableBlock, from_llm_output

from .llm import LLM

SYSTEM_PROMPT = """You are an academic presentation planner. Given evidence extracted from a paper \
and its data, produce a rigorous slide deck following academic structure (Abstract -> Methodology \
-> Experiments/Data -> Discussion -> Conclusion). Do NOT invent data or claims; every slide must \
trace to the provided evidence.

Output ONLY a single JSON object (no prose, no markdown fences) matching EXACTLY this schema:
{"deck_id": "<id>", "slides": [
  {"slide_id": "<id>",
   "layout_type": "title|section|bullet_evidence|two_column_table|formula_banner|figure_caption",
   "title": "<text>", "blocks": [<block>, ...], "provenance": {"source": "<where>"}}
]}

Each block is exactly ONE of:
  {"type": "bullets", "items": ["...", "..."]}
  {"type": "table", "columns": ["..."], "rows": [["...", "..."]]}
  {"type": "formula", "latex": "..."}
  {"type": "figure", "asset_id": "...", "caption": "..."}
Required: top-level "deck_id"; every slide needs "slide_id" and "layout_type". Do NOT add any field \
not shown above (no "content"/"body"). A title or section slide may use "blocks": [].

Example:
{"deck_id":"d1","slides":[{"slide_id":"s1","layout_type":"title","title":"Sr-Nd Isotopes","blocks":[],"provenance":{"source":"paper.txt"}},{"slide_id":"s2","layout_type":"bullet_evidence","title":"Motivation","blocks":[{"type":"bullets","items":["point A","point B"]}],"provenance":{"source":"paper.txt"}}]}"""


def _evidence_digest(
    assets: list[EvidenceAsset], tables: list[TableBlock], *, max_chars: int = 4000
) -> str:
    lines: list[str] = []
    for asset in assets:
        if asset.kind == "section_text":
            lines.append(f"[text @ {asset.source} {asset.locator}] {(asset.content_ref or '')[:600]}")
        elif asset.kind == "table":
            lines.append(f"[table @ {asset.source} {asset.locator}] ref={asset.content_ref}")
        elif asset.kind == "figure":
            lines.append(f"[figure @ {asset.source}] {asset.asset_id}")
        else:
            lines.append(f"[{asset.kind} @ {asset.source}]")
    for i, table in enumerate(tables):
        header = " | ".join(table.columns)
        sample = "; ".join(" , ".join(row) for row in table.rows[:3])
        lines.append(f"[table:{i}] cols=({header}) sample=({sample})")
    return "\n".join(lines)[:max_chars]


def build_outline_prompt(assets: list[EvidenceAsset], tables: list[TableBlock]) -> str:
    return f"Evidence:\n{_evidence_digest(assets, tables)}\n\nProduce the Slide-IR Deck JSON now."


def _extract_json(text: str) -> str:
    """Take the outermost ``{...}`` so fenced / prose-wrapped LLM output still parses."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def build_outline(assets: list[EvidenceAsset], tables: list[TableBlock], llm: LLM) -> Deck:
    """Call the LLM and parse its output through the Slide-IR boundary (rejects non-IR)."""
    prompt = build_outline_prompt(assets, tables)
    raw = llm.complete(prompt, system=SYSTEM_PROMPT)
    return from_llm_output(_extract_json(raw))  # extract JSON object, then the strict IR boundary
