"""Two-stage detailed deck builder (PPTAgent-style: skeleton -> per-slide focused expansion).

A single global call spreads thin and yields shallow bullets. Here a lightweight **skeleton** call
plans the slides (title, layout, focus, the evidence pages each draws on, optional figure), then each
slide is **expanded** by a focused call that sees only that slide's evidence at full resolution — which
is what produces depth. Assembled slides pass the strict Slide-IR boundary.
"""

from __future__ import annotations

import json
from typing import Optional

from slide_ir import Deck, EvidenceAsset, IRBoundaryError, SlideIR, TableBlock

from .llm import LLM
from .outline import _evidence_digest, _extract_json, _figure_ids

SKELETON_SYSTEM = """你是科研组会汇报的策划专家。基于论文证据,规划一份**中文**组会 deck 的骨架(8-12 页),\
遵循方法/数据论文叙事:科学问题→研究背景→数据与方法→结果与验证→讨论/机制→创新与展望。

只输出一个 JSON 对象,格式:
{"slides": [
  {"slide_id":"s1","layout_type":"title|section|bullet_evidence|two_column_table|formula_banner|figure_caption",
   "title":"<简洁一行,中文≤16字>",
   "focus":"<这页要讲清的 1-2 句核心(中文)>",
   "evidence_pages":[<用到的页码,取自证据里的 page 数字>],
   "figure_id":"<若该页以某张可用图为主,填其 asset_id;否则 null>"}
]}
规则:标题页/章节页 evidence_pages 可为 []、figure_id 为 null;以图为主的页 layout_type 用 "figure_caption" 且 figure_id 必须取自可用图列表。不要输出 schema 之外的字段,不要解释。"""

EXPAND_SYSTEM = """你在为科研组会的**一页**幻灯片生成详细内容(中文)。给你该页的 focus、可用证据原文、\
以及(可选)一张图。要做到有**深度**——讲清具体方法/数据/结论,不要空话套话。

只输出**一页** Slide-IR JSON 对象:
{"slide_id":"<沿用>","layout_type":"<沿用>","title":"<沿用或精炼>",
 "blocks":[<block>...],"speaker_notes":"<3-5 句讲稿>","provenance":{"source":"<页码/出处>"}}
block 之一:
  {"type":"bullets","items":["...","..."]}
  {"type":"figure","asset_id":"<指定的图 id>","caption":"<一句图注>"}
  {"type":"table","columns":["..."],"rows":[["..."]]}
  {"type":"formula","latex":"..."}
要求:
- bullet 给 **4-6 条有实质**的要点(具体到方法、数值、机制、结论),末条以 "→ " 开头给"这说明了什么"的解读
- speaker_notes:讲者照着念的口播稿
- 术语/符号/方法名/引用保持原文(Random Forest、SHAP、O₂、r=0.938、Lyons et al., 2014 等)
- 每条 bullet 至多一个 `**重点词或数字**`,不要滥用
- 若给了有效 figure_id:layout_type 用 "figure_caption",放一个 figure block(asset_id 用给定 id)+ 一句 caption,并另给 2-4 条要点 bullet
只输出该页 JSON,不要解释、不要 markdown 围栏。"""


def _evidence_by_page(assets: list[EvidenceAsset]) -> dict[int, str]:
    pages: dict[int, list[str]] = {}
    for a in assets:
        if a.kind == "section_text" and isinstance(a.locator, dict):
            p = a.locator.get("page")
            if p is not None:
                pages.setdefault(int(p), []).append(a.content_ref or "")
    return {p: "\n".join(v) for p, v in pages.items()}


def _figures_by_id(assets: list[EvidenceAsset]) -> dict[str, str]:
    out: dict[str, str] = {}
    for a in assets:
        if a.kind == "figure":
            cap = a.locator.get("caption", "") if isinstance(a.locator, dict) else ""
            out[a.asset_id] = cap
    return out


def _skeleton(
    assets: list[EvidenceAsset], tables: list[TableBlock], llm: LLM, feedback: Optional[list[str]]
) -> list[dict]:
    figs = _figure_ids(assets)
    fig_line = ", ".join(figs) if figs else "(无)"
    prompt = (
        f"可用图 asset_id:{fig_line}\n\n证据(节选):\n{_evidence_digest(assets, tables)}\n\n现在产出骨架 JSON。"
    )
    if feedback:
        prompt += "\n\n上一稿存在以下问题,本次修订必须全部修复:\n" + "\n".join(f"- {f}" for f in feedback)
    raw = llm.complete(prompt, system=SKELETON_SYSTEM)
    data = json.loads(_extract_json(raw))
    return data.get("slides", []) if isinstance(data, dict) else []


def _expand_slide(
    plan: dict,
    ev_by_page: dict[int, str],
    figs_by_id: dict[str, str],
    llm: LLM,
    *,
    max_attempts: int = 2,
) -> SlideIR:
    pages = plan.get("evidence_pages") or []
    ev_text = "\n\n".join(f"[第 {p} 页]\n{ev_by_page.get(int(p), '')}" for p in pages)[:6000]
    fig_id = plan.get("figure_id")
    fig_note = ""
    if fig_id and fig_id in figs_by_id:
        fig_note = f"\n本页配图 figure_id={fig_id}  图注线索:{figs_by_id[fig_id][:160]}"
    base = (
        f"页标题:{plan.get('title', '')}\n本页 focus:{plan.get('focus', '')}\n"
        f"layout_type:{plan.get('layout_type', 'bullet_evidence')}{fig_note}\n\n"
        f"可用证据原文:\n{ev_text or '(此页无正文证据,依据 focus 概述)'}\n\n现在产出该页 JSON。"
    )
    prompt = base
    last: Optional[Exception] = None
    for _ in range(max(1, max_attempts)):
        raw = llm.complete(prompt, system=EXPAND_SYSTEM)
        try:
            d = json.loads(_extract_json(raw))
            d.setdefault("slide_id", plan.get("slide_id") or "s")
            d.setdefault("layout_type", plan.get("layout_type") or "bullet_evidence")
            return SlideIR.model_validate(d)
        except Exception as err:  # malformed JSON or schema violation -> re-ask
            last = err
            prompt = base + f"\n\n上次输出无法解析为合法单页 JSON,报错:{str(err)[:300]};只返回修正后的单页 JSON。"
    raise IRBoundaryError(f"slide expansion failed for {plan.get('slide_id')}: {last}")


def build_deck_detailed(
    assets: list[EvidenceAsset],
    tables: list[TableBlock],
    llm: LLM,
    *,
    feedback: Optional[list[str]] = None,
) -> Deck:
    """Skeleton -> per-slide focused expansion -> assembled Deck (validated by the IR boundary)."""
    plans = _skeleton(assets, tables, llm, feedback)
    if not plans:
        raise IRBoundaryError("skeleton produced no slides")
    ev_by_page = _evidence_by_page(assets)
    figs_by_id = _figures_by_id(assets)
    slides = [_expand_slide(plan, ev_by_page, figs_by_id, llm) for plan in plans]
    return Deck(deck_id="deck", slides=slides)  # pydantic re-validates the assembled deck
