"""Two-stage detailed deck builder (PPTAgent-style: skeleton -> per-slide focused expansion).

A single global call spreads thin and yields shallow bullets. Here a lightweight **skeleton** call
plans the slides (title, layout, focus, the evidence pages each draws on, optional figure), then each
slide is **expanded** by a focused call that sees only that slide's evidence at full resolution — which
is what produces depth. Assembled slides pass the strict Slide-IR boundary.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from slide_ir import Deck, EvidenceAsset, IRBoundaryError, LayoutType, SlideIR, TableBlock

from .llm import LLM
from .outline import _evidence_digest, _extract_json, figure_menu, serialize_table

Progress = Optional[Callable[[dict], None]]

# Quantified density contracts per detail level (page budget incl. cover/toc/ending).
DETAIL_PROFILES: dict[str, dict[str, str]] = {
    "brief": {"pages": "5-7", "bullets": "3-4", "notes": "2-3"},
    "normal": {"pages": "8-11", "bullets": "4-6", "notes": "3-4"},
    "high": {"pages": "12-15", "bullets": "5-7", "notes": "4-5"},
}


def _detail_profile(detail: Optional[str]) -> Optional[dict[str, str]]:
    """None => "auto": the model decides page count / density from the paper itself."""
    key = (detail or "auto").lower()
    if key == "auto":
        return None
    return DETAIL_PROFILES.get(key, None)

SKELETON_SYSTEM = """你是科研组会汇报的策划专家。基于论文证据,规划一份**中文**组会 deck 的骨架,\
默认遵循方法/数据论文叙事:科学问题→研究背景→数据与方法→结果与验证→讨论/机制→创新与展望(按论文类型可增删调整)。

只输出一个 JSON 对象,格式:
{"slides": [
  {"slide_id":"s1","layout_type":"title|toc|section|ending|bullet_evidence|two_column_table|formula_banner|figure_caption|figure_left|two_content|figure_grid|big_figure",
   "title":"<简洁一行,中文≤16字>",
   "focus":"<这页要讲清的 1-2 句核心(中文)>",
   "evidence_pages":[<用到的页码,取自证据里的 page 数字>],
   "figure_ids":["<该页要用的图 asset_id,0-4 个;figure_grid 页给 2-4 个;非图页给 []>"],
   "table_refs":[<若该页要用到某些数据表,填其表索引(证据里 [表 i] 的 i);否则 []>]}
]}
- **整体结构**:第 1 页 `title`(封面)→ 第 2 页 `toc`(目录,focus 写出 3-5 个章节名)→ 正文 → 末页 `ending`(致谢/Q&A)。\
**用 `section` 章节页给正文分章**(章节名与目录条目一致;章节数量按内容定),不要让大量正文无章节地连续铺排。\n**结果/验证/讨论章节的每一章至少安排 1 个带图或图表的页**(从可用图列表选,或用 chart/stat 呈现数据)——结果章节全是纯文字 bullet 页是不合格的。
- **版式分配是设计决策**:规划时通盘考虑全 deck 的构图节奏——相邻图文页**交替** `figure_caption`(图右)/`figure_left`(图左);\
最关键的结果图用 `big_figure` 放大;2-4 张相关子图用 `figure_grid` 对比;表格页用 `two_column_table`;\
避免连续多页同一种版式(单调感是低质量 deck 的主要特征);确有理由时可以例外。
- **严禁冗余**:不要出现两页讲同一个要点/同一张图/同一组数据,每页的 title 与 focus 必须覆盖不同内容,不要把一个结果拆成近乎重复的两页。
- **不规划单薄页**:某个要点若只有两三句可讲,并入相邻页,不要单列;`figure_grid` 仅在确有 2-4 张同主题子图时使用,只有一张图就用 figure_caption/figure_left。
- **版式语义**:`title`/`section`/`ending` 是**分隔页**,只有标题、不承载正文;只要本页有实质内容要讲,用内容版式,不要错用 `section`。
- 规则:分隔页 evidence_pages/figure_ids/table_refs 均为空;图为主的页 figure_ids 必须取自可用图列表;\
**若有补充数据表值得展示/作图,在相应页填 table_refs**(扩写阶段会拿到该表完整数据)。
不要输出 schema 之外的字段,不要解释。"""

PREMIUM_SKELETON_NOTE = """
- **精品档**:对最关键的 2-3 个结果/机制页,可用 layout_type `canvas` 做自由构图(信息卡片组/方法对照表/带注释的数据图)——canvas 页表达力最强但成本高,只用在最值得的页;其余页仍用常规版式。"""

CANVAS_SYSTEM = """你在为科研组会的单页幻灯片做**自由构图**(精品档)。直接创作整页 SVG,像专业设计师一样排版:信息卡片组、方法/前人工作对照表、带参考线和标注的数据图、机制示意——构图由你决定。

硬约束(违反即被拒绝):
- 画布 viewBox 必须是 "0 0 1280 720";只允许矢量与文本元素:rect/circle/ellipse/line/polyline/polygon/path/text/g/defs
- **禁止** script/foreignObject/image/动画/外部引用(href 只允许 "#内部" 形式);特殊字符必须 XML 转义(& 写成 &amp;)
- 调色板:正文 #333333、强调/标题点缀 #8B1A1A、卡片底 #F5F7FA、边框 #D0D7E0、辅助灰 #808080、白 #FFFFFF
- 字体:font-family 中文 "SimHei"、数字与英文 "Times New Roman";字号 12-40px;**每行文字一个独立 <text>**(导出后逐行可编辑)
- 顶部 y=60-100 放页标题(28-32px #333 粗体)与一句导读(14px #808080);内容区 y=130-680;对齐严格、留白充足
- 文字行宽自己估算(中文≈字号 px/字),**绝不能溢出所在卡片/区域**;几何(网格/坐标轴/比例)要按数据计算,不要随手乱画
- **所有数字与结论必须来自给定证据,严禁编造**

只输出该页 JSON(不要解释、不要围栏):
{"slide_id":"<沿用>","layout_type":"canvas","title":"<页标题>","subtitle":"<一句导读>",
 "blocks":[{"type":"canvas","svg":"<整页 SVG 字符串>"}],"speaker_notes":"<口播稿>","provenance":{"source":"<页码>"}}"""

EXPAND_SYSTEM = """你在为科研组会的**一页**幻灯片生成详细内容(中文)。给你该页的 focus、可用证据原文、\
以及(可选)一张图。要做到有**深度**——讲清具体方法/数据/结论,不要空话套话。

只输出**一页** Slide-IR JSON 对象:
{"slide_id":"<沿用>","layout_type":"<沿用>","title":"<沿用或精炼>",
 "subtitle":"<内容页:一句话本页导读(短到放进一行,讲清本页核心发现/要点);封面:论文出处或英文原题;section/ending:一句导语;可为空>",
 "blocks":[<block>...],"speaker_notes":"<3-4 句讲稿>","provenance":{"source":"<页码/出处>"}}
block 之一:
  {"type":"bullets","items":["...", {"text":"<要点>","children":["<子要点>","..."]}]}(子要点最多一层,仅在确有从属关系时用)
  {"type":"figure","asset_id":"<指定的图 id>","caption":"<一句图注>"}
  {"type":"table","columns":["..."],"rows":[["..."]]}
  {"type":"formula","latex":"..."}
  {"type":"chart","chart_type":"bar|line|scatter|pie","categories":["..."],"series":[{"name":"...","values":[1,2,3]}],"title":"..."}
  {"type":"diagram","diagram_type":"flow|tree|cycle|comparison|pyramid|timeline","nodes":[{"id":"n1","label":"..."}],"edges":[{"source":"n1","target":"n2","label":"..."}],"title":"..."}
  {"type":"callout","label":"结论","text":"<一句话核心结论/启示>","icon":"bulb"}(本页有明确核心结论时,可用它替代最后一条 "→ " bullet)
  {"type":"stat","items":[{"value":"r=0.938","label":"验证集相关系数","icon":"target"}]}(1-4 个**来自证据的**关键数值,适合成果/指标页;严禁编造)
图标(callout/stat 的可选 icon 字段):填 Tabler outline 图标名(常用如 database, chart-bar, flask, microscope, atom, target, bulb, alert-triangle, mountain, droplet, thermometer, gauge;**任意合法 Tabler 名称都可**,未知名会被自动跳过)。**仅在概念确实匹配时使用,克制为美**;没有合适的就省略 icon 字段。
要求:
- **图表(chart)**:若本页证据里有一组可比较的数值(≥3 个类别/时间点/分组的指标,如各元素重要性、随时间的指标),\
**优先输出 chart block 用原生图表可视化**,而不是仅用文字罗列。**选型**:类别间对比→`bar`;随时间/自变量的趋势→`line`;\
占比/构成→`pie`;两变量相关性→`scatter`(用每个 series 的 `x` 与 `values` 配对)。`series.values` 与 `categories` 一一对应。\
**所有数字必须直接来自证据,严禁编造或估算**;证据里没有具体数值就不要出图表。
- **逻辑图件(diagram)**:若本页讲的是一个**流程/步骤、方法对比、循环、层级、金字塔、时间线**等逻辑关系,\
**优先输出 diagram block** 用原生图形表达,而不是堆 bullet。你只给**语义结构**(`nodes` 节点 + `edges` 有向边,`id` 自取、`label` 简短),\
**不要给坐标**(版面由系统自动排)。flow/timeline 的 edges 可省略(按 nodes 顺序连)。**节点与关系必须来自论文,严禁编造**。
- bullet 数量按本页内容决定,**每条都要有实质**(具体到方法、数值、机制、结论);**结果/验证/讨论页**最后一条以 "→ " 开头给出\
"这说明了什么"的解读,或改用一个 callout block 表达该解读(数据/方法页可省略)
- speaker_notes:讲者照着念的口播稿,**3-4 句即可**
- **简洁高密度**:每条 bullet 一句话讲清、放得进一行,不要冗长展开、不要重复正文;整页输出尽量精炼
- **构图预算**:每页**至多 3 个 block**——至多 1 个重图形块(figure/chart/diagram/table)、至多 1 个轻强调块(callout 或 stat,二选一)、其余为 bullets;塞不下就精简,**不要四种块挤一页**;反之只有一个 callout 加两三条 bullet 的页面过空——要么充实要点,要么本就不该单列此页
- **版式一致**:若 layout_type 是 `title`/`section`/`ending`(分隔页),只给标题、不要输出任何内容 block;若本页确有正文要讲,本就不该是分隔页,请按 `bullet_evidence` 产出正文
- **目录页**:若 layout_type 是 `toc`,只输出一个 bullets block,每条是一个章节名(与章节页一致,短语,不带解读),不要 "→ " 结尾条
- 术语/符号/方法名/引用保持原文(Random Forest、SHAP、O₂、r=0.938、Lyons et al., 2014 等);**论文核心术语全篇统一**(如 hygrometer=湿度计/含水量计,绝不可与温度计/温压计混写)
- `**强调**`只给承载结论的关键词或数字,**宁少勿多**——强调泛滥等于没有强调
- 若给了有效图 id:**沿用骨架规划的图类版式**(figure_caption/figure_left/big_figure/figure_grid),放对应 figure block(**asset_id 必须一字不差照抄给定 id**,grid 页放多个)+ 一句 caption,并配要点 bullet
- **caption 写实**:图注只描述所选图**当前画面**;若是拆分出的子图,不要提及其它子图的字母(A/B/C)或内容
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


_STRUCTURAL_LAYOUTS = {LayoutType.TITLE, LayoutType.SECTION, LayoutType.ENDING}
_CONTENT_BLOCK_TYPES = {"bullets", "table", "figure", "chart", "diagram", "formula", "callout", "stat", "canvas"}


def _norm_title(t: str) -> str:
    """Lowercase, drop whitespace/ASCII punctuation; keep CJK so Chinese titles don't collapse.

    Unicode mode (no re.ASCII): \\w matches CJK, so \\W strips only punctuation/space, not CJK chars.
    """
    return re.sub(r"[\s\W_]+", "", (t or "").lower())


def _dedup_plans(plans: list[dict], *, ratio: float = 0.86) -> list[dict]:
    """Drop near-duplicate skeleton plans (same point/chart) before the expensive expansion.

    char-level SequenceMatcher on normalized title+focus (CJK-safe; keep the first of each cluster).
    """
    kept: list[dict] = []
    keys: list[str] = []
    for p in plans:
        key = _norm_title(f"{p.get('title', '')} {p.get('focus', '')}")
        if any(k == key or difflib.SequenceMatcher(None, key, k).ratio() >= ratio for k in keys):
            continue
        kept.append(p)
        keys.append(key)
    return kept


def _normalize_blocks(d: dict) -> dict:
    """Deterministic pre-validation cleanup of high-frequency LLM near-misses: a table's ``title``
    becomes its ``caption`` (TableBlock has no title field; models add one constantly)."""
    for b in d.get("blocks", []) or []:
        if isinstance(b, dict) and b.get("type") == "table" and "title" in b:
            title = b.pop("title")
            if title and not b.get("caption"):
                b["caption"] = title
    return d


def _fix_structural_layout(slide: SlideIR) -> SlideIR:
    """A divider (title/section) carrying content blocks is a misselection — relayout to bullets."""
    if slide.layout_type in _STRUCTURAL_LAYOUTS and any(b.type in _CONTENT_BLOCK_TYPES for b in slide.blocks):
        return slide.model_copy(update={"layout_type": LayoutType.BULLET_EVIDENCE})
    return slide


def _skeleton(
    assets: list[EvidenceAsset],
    tables: list[TableBlock],
    llm: LLM,
    feedback: Optional[list[str]],
    detail: str = "auto",
    premium: bool = False,
) -> list[dict]:
    menu = figure_menu(assets)
    fig_line = f"\n{menu}\n(figure_ids 按图注语义选择,**优先有图注的结果图**,无图注的慎用)" if menu else "(无)"
    prof = _detail_profile(detail)
    if prof is None:  # auto: the page count is the model's call, driven by the paper's content
        density = (
            "页数由你决定:每个值得讲透的结果/方法要点一页,讲透为准——不为凑页数而拆分,也不为省页数而合并;"
            "结构页(封面/目录/章节/致谢)另算。"
        )
    else:
        density = f"密度目标(可按内容增减):**正文内容页**约 {prof['pages']} 页(结构页另算,不要用结构页凑数)。"
    prompt = (
        f"可用图:{fig_line}\n\n证据(节选):\n{_evidence_digest(assets, tables)}\n\n"
        f"{density}\n现在产出骨架 JSON。"
    )
    if feedback:
        prompt += "\n\n上一稿存在以下问题,本次修订必须全部修复:\n" + "\n".join(f"- {f}" for f in feedback)
    system = SKELETON_SYSTEM + (PREMIUM_SKELETON_NOTE if premium else "")
    raw = llm.complete(prompt, system=system)
    data = json.loads(_extract_json(raw))
    slides = data.get("slides", []) if isinstance(data, dict) else []
    return _dedup_plans(slides)


def _expand_slide(
    plan: dict,
    ev_by_page: dict[int, str],
    figs_by_id: dict[str, str],
    llm: LLM,
    tables: Optional[list[TableBlock]] = None,
    *,
    max_attempts: int = 2,
    detail: str = "auto",
) -> SlideIR:
    pages = plan.get("evidence_pages") or []
    fig_ids = [f for f in (plan.get("figure_ids") or ([plan["figure_id"]] if plan.get("figure_id") else [])) if f]
    # adaptive cap: figure/table slides keep full context; plain bullet slides are already focused.
    cap = 9000 if (fig_ids or plan.get("table_refs")) else 6000
    ev_text = "\n\n".join(f"[第 {p} 页]\n{ev_by_page.get(int(p), '')}" for p in pages)[:cap]
    fig_note = ""
    known = [f for f in fig_ids if f in figs_by_id]
    if known:
        lines = "\n".join(f"- {f}  图注线索:{figs_by_id[f][:400]}" for f in known)
        fig_note = f"\n本页配图({len(known)} 张):\n{lines}"
    data_note = ""
    all_tables = tables or []
    refs = [r for r in (plan.get("table_refs") or []) if isinstance(r, int) and 0 <= r < len(all_tables)]
    if refs:
        blocks = "\n\n".join(f"[表 {r}]\n{serialize_table(all_tables[r])}" for r in refs)
        data_note = (
            f"\n\n本页可用数据表(原始数值,可据此出 chart 或讨论,数字必须取自这里):\n{blocks}"
        )
    prof = _detail_profile(detail)
    if prof is None:
        density = "要点数量由本页内容决定(图表页两三条即可,方法页可以更多),每条都要有实质;讲稿简洁口语化。"
    else:
        density = f"密度目标(按内容可增减):本页 bullets 约 {prof['bullets']} 条、speaker_notes 约 {prof['notes']} 句。"
    base = (
        f"页标题:{plan.get('title', '')}\n本页 focus:{plan.get('focus', '')}\n"
        f"layout_type:{plan.get('layout_type', 'bullet_evidence')}{fig_note}\n\n"
        f"可用证据原文:\n{ev_text or '(此页无正文证据,依据 focus 概述)'}{data_note}\n\n"
        f"{density}\n现在产出该页 JSON。"
    )
    is_canvas = (plan.get("layout_type") or "") == "canvas"
    system = CANVAS_SYSTEM if is_canvas else EXPAND_SYSTEM
    attempts = max_attempts + 1 if is_canvas else max_attempts  # SVG authoring earns one extra try
    if is_canvas:
        from .exemplars import pick_exemplar

        ex = pick_exemplar(plan.get("title"), plan.get("focus"))
        if ex:
            base += (
                f"\n\n构图范例(类型:{ex[0]};**仅参考布局与表达手法**——配色换成本提示规定的调色板,"
                f"文字与数据一律来自上面的证据,不要照抄范例内容):\n{ex[1]}"
            )
    prompt = base
    last: Optional[Exception] = None
    for _ in range(max(1, attempts)):
        raw = llm.complete(prompt, system=system)
        try:
            d = _normalize_blocks(json.loads(_extract_json(raw)))
            d.setdefault("slide_id", plan.get("slide_id") or "s")
            d.setdefault("layout_type", plan.get("layout_type") or "bullet_evidence")
            slide = _fix_structural_layout(SlideIR.model_validate(d))
            if is_canvas:  # the canvas guard is part of the boundary: invalid SVG re-asks
                issues = _canvas_issues(slide)
                if issues:
                    raise ValueError("; ".join(issues)[:400])
            return slide
        except Exception as err:  # malformed JSON / schema violation / canvas-guard issue -> re-ask
            last = err
            prompt = base + f"\n\n上次输出无法通过校验,问题:{str(err)[:400]};只返回修正后的单页 JSON。"
    if is_canvas:  # fail open: degrade the canvas plan to a regular page rather than killing the run
        fallback = dict(plan)
        fallback["layout_type"] = "bullet_evidence"
        return _expand_slide(fallback, ev_by_page, figs_by_id, llm, tables, max_attempts=max_attempts, detail=detail)
    raise IRBoundaryError(f"slide expansion failed for {plan.get('slide_id')}: {last}")


def _canvas_issues(slide: SlideIR) -> list[str]:
    canvas_blocks = [b for b in slide.blocks if b.type == "canvas"]
    if len(canvas_blocks) != 1:
        return ["canvas 页必须且只能有一个 canvas block"]
    try:
        from pptx_compiler import lint_canvas_svg, validate_canvas_svg
    except Exception:
        return []
    issues = validate_canvas_svg(canvas_blocks[0].svg)
    if not issues:  # geometry lint only once the canvas is structurally valid
        issues = lint_canvas_svg(canvas_blocks[0].svg)
    return issues


_REPAIR_SYSTEM = """你在修正一页已生成的科研幻灯片。给你该页当前 JSON 和它的问题清单,请**只修复这些问题**,\
保持该页主题、证据、术语、配图/图表/图件不变。重新输出**该页**合法 Slide-IR JSON(同 schema:slide_id/\
layout_type/title/blocks/speaker_notes/provenance)。
若问题是「图类版式但无 figure block」:你没有可用图清单,**把 layout_type 改为 bullet_evidence**,不要发明 asset_id。
若问题是「figure_grid 不足两张图」:把 layout_type 改为 figure_caption(保留现有图),不要发明新图。
block 的 type **只能是**:bullets / figure / table / formula / chart / diagram / callout / stat / canvas,\
不存在其它容器或栏位类型(版面由 layout_type 决定,不要发明 "column" 之类的块)。
不要解释、不要 markdown 围栏。"""

_SLIDE_REF = re.compile(r"slide '([^']+)'")


def _bad_ids(feedback: list[str]) -> dict[str, list[str]]:
    """Map flagged slide_id -> its findings, parsed from critic finding strings."""
    out: dict[str, list[str]] = {}
    for f in feedback:
        m = _SLIDE_REF.search(f)
        if m:
            out.setdefault(m.group(1), []).append(f)
    return out


def _repair_slide(slide: SlideIR, findings: list[str], llm: LLM, *, max_attempts: int = 2) -> SlideIR:
    base = (
        f"当前这页 JSON:\n{slide.model_dump_json()}\n\n这页存在的问题:\n"
        + "\n".join(f"- {f}" for f in findings)
        + "\n\n请只修复这些问题,重新输出该页 JSON。"
    )
    prompt = base
    last: Optional[Exception] = None
    for _ in range(max(1, max_attempts)):
        raw = llm.complete(prompt, system=_REPAIR_SYSTEM)
        try:
            d = _normalize_blocks(json.loads(_extract_json(raw)))
            d.setdefault("slide_id", slide.slide_id)
            d.setdefault("layout_type", slide.layout_type.value)
            return _fix_structural_layout(SlideIR.model_validate(d))
        except Exception as err:
            last = err
            prompt = base + f"\n\n上次输出无法解析:{str(err)[:200]};只返回修正后的单页 JSON。"
    raise IRBoundaryError(f"repair failed for {slide.slide_id}: {last}")


def _emit(progress: Progress, event: dict) -> None:
    if progress:
        try:
            progress(event)
        except Exception:  # progress is best-effort; never let it break generation
            pass


def build_deck_detailed(
    assets: list[EvidenceAsset],
    tables: list[TableBlock],
    llm: LLM,
    *,
    feedback: Optional[list[str]] = None,
    progress: Progress = None,
    parallel: bool = True,
    max_workers: Optional[int] = None,
    prior_slides: Optional[list[SlideIR]] = None,
    detail: str = "auto",
    premium: bool = True,
) -> Deck:
    """Skeleton -> per-slide focused expansion -> assembled Deck (validated by the IR boundary).

    Slides are expanded in parallel by default (each is independent; calls are I/O-bound); on any
    worker failure it falls back to serial. ``progress`` is called for the skeleton and each slide.

    On a critic retry (``prior_slides`` + ``feedback``), only the flagged slides are repaired and the
    rest are kept verbatim — no skeleton call, no re-expanding good slides.
    """
    if prior_slides and feedback:
        bad = _bad_ids(feedback)
        global_fb = [f for f in feedback if not _SLIDE_REF.search(f)]
        if global_fb:  # user rejection / deck-level findings: a full replan, not a per-slide patch
            titles = " / ".join(s.title for s in prior_slides if s.title)
            feedback = list(feedback) + [f"(上一稿大纲,供改进参考: {titles[:600]})"]
            prior_slides = None
    if prior_slides and feedback and bad:
        total = len(prior_slides)
        _emit(progress, {"phase": "repair", "total": total})
        repaired: list[SlideIR] = []
        for i, s in enumerate(prior_slides):
            if s.slide_id in bad:
                try:
                    s = _repair_slide(s, bad[s.slide_id], llm)
                except IRBoundaryError:  # fail open: keep the original; the finding reaches the human
                    _emit(progress, {"phase": "repair_kept_original", "slide_id": s.slide_id})
            repaired.append(s)
            _emit(progress, {"phase": "slide", "done": i + 1, "total": total})
        return Deck(deck_id="deck", slides=repaired)

    _emit(progress, {"phase": "skeleton"})
    plans = _skeleton(assets, tables, llm, feedback, detail, premium)
    if not plans:
        raise IRBoundaryError("skeleton produced no slides")
    total = len(plans)
    _emit(progress, {"phase": "skeleton_done", "total": total})
    ev_by_page = _evidence_by_page(assets)
    figs_by_id = _figures_by_id(assets)

    workers = max_workers or int(os.environ.get("ASA_EXPAND_WORKERS", "6") or "6")
    debug_timing = bool(os.environ.get("ASA_DEBUG_TIMING"))
    durations: list[float] = []

    def expand(plan: dict) -> SlideIR:
        if not debug_timing:
            return _expand_slide(plan, ev_by_page, figs_by_id, llm, tables, detail=detail)
        t0 = time.perf_counter()
        try:
            return _expand_slide(plan, ev_by_page, figs_by_id, llm, tables, detail=detail)
        finally:
            durations.append(time.perf_counter() - t0)

    slides: list[Optional[SlideIR]] = [None] * total
    if parallel and total > 1:
        try:
            wave_start = time.perf_counter() if debug_timing else None
            with ThreadPoolExecutor(max_workers=min(workers, total)) as pool:
                futures = {pool.submit(expand, plan): i for i, plan in enumerate(plans)}
                done = 0
                for fut in as_completed(futures):
                    slides[futures[fut]] = fut.result()  # propagates worker exceptions
                    done += 1
                    _emit(progress, {"phase": "slide", "done": done, "total": total})
            if wave_start is not None:  # probe: wall ≈ sum ⇒ gateway is serializing concurrency
                wall = time.perf_counter() - wave_start
                _emit(progress, {"phase": "timing", "wall_s": round(wall, 1), "sum_s": round(sum(durations), 1), "concurrency": round(sum(durations) / max(wall, 0.01), 2)})
            return Deck(deck_id="deck", slides=[s for s in slides if s is not None])
        except Exception:
            _emit(progress, {"phase": "fallback_serial"})  # parallel failed -> serial below

    serial: list[SlideIR] = []
    for i, plan in enumerate(plans):
        serial.append(expand(plan))
        _emit(progress, {"phase": "slide", "done": i + 1, "total": total})
    return Deck(deck_id="deck", slides=serial)  # pydantic re-validates the assembled deck
