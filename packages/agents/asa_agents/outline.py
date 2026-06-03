"""Outline agent: Evidence Pool -> Slide-IR Deck, enforcing the IR boundary.

The LLM's output is parsed through ``from_llm_output``, so prose/code/HTML are rejected and never
reach the compiler ("LLM locked to IR", docs/SPEC.md §3.1).
"""

from __future__ import annotations

from typing import Optional

from slide_ir import Deck, EvidenceAsset, TableBlock, from_llm_output

from .llm import LLM

SYSTEM_PROMPT = """你是一名科研组会/学术报告的幻灯片策划专家。给你一篇论文及其数据中抽取的证据,\
产出一份**中文**组会汇报 deck。受众是同领域研究生与导师。

叙事结构(方法/数据类论文,按需增删页):
1) 标题页:一句话讲清这项工作 + 用 speaker_notes 写明核心科学问题
2) 研究背景 / 科学问题:为什么做、前人到哪一步
3) 数据与方法:数据来源与特征(X)、标签与模型(Y),可分多页
4) 结果与验证:每个关键结果/分析一页(如建模结果、特征重要性、周期分析)
5) 讨论 / 机制:结果说明了什么机制
6) 创新点与展望:方法创新、局限、下一步

每一页内容要求:
- 标题:**简洁一行**(中文≤16字),不要把论文长标题原样倒进去
- 2–5 条要点 bullet,准确、可溯源,不要编造数据
- 末尾加一条以 "→ " 开头的**解读句**,讲"这说明了什么"
- speaker_notes:2–4 句口播稿(讲者照着念)
- 术语、元素符号、方法名、文献引用保持原文(如 Random Forest、SHAP、Monte Carlo、O₂、Mo、Lyons et al., 2014)
- 每条 bullet 至多把一个最关键的词或数字用 **…** 包起来表示重点(编译器会渲染成红色加粗),不要滥用

配图规则:只允许引用"可用图 asset_id"列表中确实存在的 id;若该列表为空或某图不在其中,\
**不要**输出 figure block,而是用一条 bullet 文字描述该图(如 "论文 Fig.2:大气 O₂ 演化重建曲线")。

只输出一个 JSON 对象(不要任何解释、不要 markdown 代码围栏),严格匹配以下 schema:
{"deck_id": "<id>", "slides": [
  {"slide_id": "<id>",
   "layout_type": "title|section|bullet_evidence|two_column_table|formula_banner|figure_caption",
   "title": "<简短标题>", "blocks": [<block>, ...],
   "speaker_notes": "<口播稿>", "provenance": {"source": "<出处>"}}
]}

每个 block 恰好是以下之一:
  {"type": "bullets", "items": ["...", "..."]}
  {"type": "table", "columns": ["..."], "rows": [["...", "..."]]}
  {"type": "formula", "latex": "..."}
  {"type": "figure", "asset_id": "<必须在可用列表中>", "caption": "..."}
必填:顶层 "deck_id";每页 "slide_id" 与 "layout_type"。不要添加 schema 之外的字段(如 "content"/"body")。\
标题页/章节页可用 "blocks": []。

示例:
{"deck_id":"d1","slides":[{"slide_id":"s1","layout_type":"title","title":"机器学习重建地球 35 亿年大气氧演化","blocks":[],"speaker_notes":"本工作要回答:大气 O₂ 的长期上升与叠加波动,分别由什么驱动?","provenance":{"source":"paper p1"}},{"slide_id":"s2","layout_type":"bullet_evidence","title":"研究背景","blocks":[{"type":"bullets","items":["大气增氧是地表环境与复杂生命演化的关键","但驱动**长期波动**的机制仍不清楚","论文 Fig.1:前人重建的 O₂ 演化曲线(Lyons et al., 2014)"]}],"speaker_notes":"先交代为什么这个问题重要,以及前人方法的局限。","provenance":{"source":"paper p1-2"}}]}"""


def _evidence_digest(
    assets: list[EvidenceAsset], tables: list[TableBlock], *, max_chars: int = 12000
) -> str:
    lines: list[str] = []
    for asset in assets:
        if asset.kind == "section_text":
            lines.append(f"[text @ {asset.source} {asset.locator}] {(asset.content_ref or '')[:1500]}")
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


def _figure_ids(assets: list[EvidenceAsset]) -> list[str]:
    return [a.asset_id for a in assets if a.kind == "figure"]


def build_outline_prompt(assets: list[EvidenceAsset], tables: list[TableBlock]) -> str:
    figs = _figure_ids(assets)
    fig_line = ", ".join(figs) if figs else "(无 — 不要输出任何 figure block,用文字描述图)"
    return (
        f"可用图 asset_id:{fig_line}\n\n"
        f"证据:\n{_evidence_digest(assets, tables)}\n\n现在产出 Slide-IR Deck JSON。"
    )


def _extract_json(text: str) -> str:
    """Take the outermost ``{...}`` so fenced / prose-wrapped LLM output still parses."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def build_outline(
    assets: list[EvidenceAsset],
    tables: list[TableBlock],
    llm: LLM,
    *,
    feedback: Optional[list[str]] = None,
) -> Deck:
    """Call the LLM and parse its output through the Slide-IR boundary (rejects non-IR).

    ``feedback`` carries the critic's findings from a prior pass so the planner fixes them on retry.
    """
    prompt = build_outline_prompt(assets, tables)
    if feedback:
        issues = "\n".join(f"- {f}" for f in feedback)
        prompt += "\n\n上一稿存在以下问题,本次修订必须全部修复:\n" + issues
    raw = llm.complete(prompt, system=SYSTEM_PROMPT)
    return from_llm_output(_extract_json(raw))  # extract JSON object, then the strict IR boundary
