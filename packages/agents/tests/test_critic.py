"""Critic + retry-loop tests.

Each test maps to a scenario in openspec/changes/add-critic-loop/specs/critic/spec.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from langgraph.types import Command

from slide_ir import (
    BulletBlock,
    DiagramBlock,
    DiagramEdge,
    DiagramNode,
    EvidenceAsset,
    FigureBlock,
    GenerationState,
    LayoutType,
    SlideIR,
    TableBlock,
)
from asa_agents import FakeLLM, critique_deck
from asa_agents.graph import build_graph

_EVIDENCE = [
    EvidenceAsset(asset_id="fig1", kind="figure", content_ref="fig1.png", source="paper.pdf")
]


def _clean_slides() -> list[SlideIR]:
    return [
        SlideIR(slide_id="s1", layout_type=LayoutType.TITLE, title="A Study", blocks=[]),
        SlideIR(
            slide_id="s2",
            layout_type=LayoutType.BULLET_EVIDENCE,
            title="Motivation",
            blocks=[BulletBlock(items=["a", "b", "c", "→ d"])],
        ),
        SlideIR(
            slide_id="s3",
            layout_type=LayoutType.FIGURE_CAPTION,
            title="Result",
            blocks=[FigureBlock(asset_id="fig1", caption="c")],
        ),
    ]


def test_clean_deck_has_no_findings():
    assert critique_deck(_clean_slides(), _EVIDENCE) == []


def test_chart_satisfies_two_column_table_layout():
    from slide_ir import ChartBlock, ChartSeries

    slides = [
        SlideIR(
            slide_id="c",
            layout_type=LayoutType.TWO_COLUMN_TABLE,
            title="data",
            blocks=[ChartBlock(chart_type="bar", categories=["A", "B"], series=[ChartSeries(name="x", values=[1.0, 2.0])])],
        )
    ]
    assert not any("two_column_table" in f for f in critique_deck(slides, []))  # chart counts as data block


def test_diagram_dangling_edge_flagged():
    slides = [
        SlideIR(
            slide_id="d1",
            layout_type=LayoutType.BULLET_EVIDENCE,
            title="x",
            blocks=[
                DiagramBlock(
                    diagram_type="flow",
                    nodes=[DiagramNode(id="a", label="A")],
                    edges=[DiagramEdge(source="a", target="ghost")],
                )
            ],
        )
    ]
    assert any("undefined node" in f for f in critique_deck(slides, []))


def test_each_defect_is_flagged():
    slides = [
        # empty content slide + empty title
        SlideIR(slide_id="empty", layout_type=LayoutType.BULLET_EVIDENCE, title="", blocks=[]),
        # bullet overflow (8 > 7) + an over-long item
        SlideIR(
            slide_id="bul",
            layout_type=LayoutType.BULLET_EVIDENCE,
            title="x",
            blocks=[BulletBlock(items=[str(i) for i in range(11)] )],
        ),
        # table overflow (7 cols, 13 rows)
        SlideIR(
            slide_id="tab",
            layout_type=LayoutType.TWO_COLUMN_TABLE,
            title="x",
            blocks=[TableBlock(columns=[f"c{i}" for i in range(7)], rows=[["1"] * 7 for _ in range(13)])],
        ),
        # layout/block mismatch: formula_banner without a formula
        SlideIR(slide_id="fb", layout_type=LayoutType.FORMULA_BANNER, title="x", blocks=[BulletBlock(items=["q"])]),
        # dangling figure asset_id
        SlideIR(
            slide_id="fig",
            layout_type=LayoutType.FIGURE_CAPTION,
            title="x",
            blocks=[FigureBlock(asset_id="ghost")],
        ),
    ]
    findings = critique_deck(slides, _EVIDENCE)
    joined = " || ".join(findings)
    assert "empty title" in joined
    assert "no blocks" in joined
    assert "bullet list too long" in joined
    assert "table too wide" in joined and "table too tall" in joined
    assert "no formula block" in joined
    assert "unknown asset_id 'ghost'" in joined


# --- Retry loop in the graph -------------------------------------------------

_DEFECT_DECK = json.dumps(
    {
        "deck_id": "j1",
        "slides": [
            {
                "slide_id": "s1",
                "layout_type": "bullet_evidence",
                "title": "M",
                "blocks": [{"type": "bullets", "items": [str(i) for i in range(11)]}],
            }
        ],
    }
)

_CLEAN_DECK = json.dumps(
    {
        "deck_id": "j1",
        "slides": [
            {
                "slide_id": "s1",
                "layout_type": "bullet_evidence",
                "title": "M",
                "blocks": [{"type": "bullets", "items": ["a", "b", "c", "→ d"]}],
            }
        ],
    }
)


def _init() -> dict:
    return GenerationState(
        job_id="j1",
        evidence=[EvidenceAsset(asset_id="p1", kind="section_text", content_ref="t", source="paper.pdf")],
    ).model_dump()


def test_self_correction_reaches_approval_clean(tmp_path):
    # First draft is defective; given feedback, the planner emits a clean deck.
    llm = FakeLLM(_DEFECT_DECK, _CLEAN_DECK)
    graph = build_graph(llm, out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "c1"}}
    graph.invoke(_init(), cfg)
    snap = graph.get_state(cfg)
    assert "approval" in snap.next  # reached the Hard-Stop
    assert snap.values["critic_findings"] == []  # corrected
    assert snap.values["retry_count"] == 1  # exactly one re-plan
    assert len(llm.calls) == 2
    # the retry prompt carried the feedback
    assert "必须全部修复" in llm.calls[1]["prompt"]


def test_budget_exhaustion_still_reaches_human(tmp_path):
    # Planner never fixes the defect; loop must stop after max_retries (default 2).
    graph = build_graph(FakeLLM(_DEFECT_DECK), out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "c2"}}
    graph.invoke(_init(), cfg)
    snap = graph.get_state(cfg)
    assert "approval" in snap.next  # still handed to the human
    assert snap.values["retry_count"] == 2  # max_retries
    assert snap.values["critic_findings"]  # residual findings recorded


def test_budget_exhaustion_then_approve_compiles(tmp_path):
    graph = build_graph(FakeLLM(_DEFECT_DECK), out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "c3"}}
    graph.invoke(_init(), cfg)
    final = graph.invoke(Command(resume={"approved": True}), cfg)
    out = final.get("output_path") if isinstance(final, dict) else getattr(final, "output_path", None)
    assert out and Path(out).exists()  # best-effort deck still compiles after human approval


# --- dedup + layout misselection ---------------------------------------------


def test_structural_layout_with_content_flagged():
    s = SlideIR(slide_id="s9", layout_type=LayoutType.SECTION, title="Results", blocks=[BulletBlock(items=["x"])])
    findings = critique_deck([s], [])
    hit = [f for f in findings if "divider but carries content" in f]
    assert hit and "slide 's9'" in hit[0]  # repair-routable


def test_structural_layout_empty_is_clean():
    s = SlideIR(slide_id="s9", layout_type=LayoutType.SECTION, title="Methods", blocks=[])
    assert not any("divider but carries content" in f for f in critique_deck([s], []))


def test_duplicate_titles_flagged_but_not_repair_routable():
    slides = [
        SlideIR(slide_id="s1", layout_type=LayoutType.BULLET_EVIDENCE, title="质量与数量阈值的权衡", blocks=[BulletBlock(items=["a"])]),
        SlideIR(slide_id="s2", layout_type=LayoutType.BULLET_EVIDENCE, title="质量数量阈值权衡", blocks=[BulletBlock(items=["b"])]),
    ]
    findings = critique_deck(slides, [])
    dup = [f for f in findings if "near-duplicate" in f]
    assert dup and "s1" in dup[0] and "s2" in dup[0]
    assert "slide '" not in dup[0]  # deliberately NOT repair-routable -> reaches the human


def test_distinct_titles_not_flagged():
    slides = [
        SlideIR(slide_id="s1", layout_type=LayoutType.BULLET_EVIDENCE, title="研究背景", blocks=[BulletBlock(items=["a"])]),
        SlideIR(slide_id="s2", layout_type=LayoutType.BULLET_EVIDENCE, title="实验结果", blocks=[BulletBlock(items=["b"])]),
    ]
    assert not any("near-duplicate" in f for f in critique_deck(slides, []))


# --- P1: layout monotony + toc consistency ------------------------------------


def _content_slide(i, layout=LayoutType.BULLET_EVIDENCE):
    return SlideIR(slide_id=f"m{i}", layout_type=layout, title=f"页{i}", blocks=[BulletBlock(items=[f"x{i}"])])


def test_layout_monotony_flagged():
    slides = [_content_slide(i) for i in range(5)]  # 5 consecutive bullet_evidence
    findings = critique_deck(slides, [])
    hit = [f for f in findings if "consecutive slides share" in f]
    assert hit and "slide '" not in hit[0]  # advisory: reaches the human, never burns the repair budget


def test_layout_variety_not_flagged():
    layouts = [LayoutType.BULLET_EVIDENCE, LayoutType.BULLET_EVIDENCE, LayoutType.BULLET_EVIDENCE]
    slides = [_content_slide(i, l) for i, l in enumerate(layouts)]  # run of 3 == allowed
    assert not any("consecutive" in f for f in critique_deck(slides, []))


def test_section_divider_resets_monotony_run():
    slides = [_content_slide(0), _content_slide(1), SlideIR(slide_id="d", layout_type=LayoutType.SECTION, title="结果", blocks=[]), _content_slide(2), _content_slide(3)]
    assert not any("consecutive" in f for f in critique_deck(slides, []))


def test_toc_without_bullets_flagged():
    s = SlideIR(slide_id="t", layout_type=LayoutType.TOC, title="目录", blocks=[])
    findings = critique_deck([s], [])
    assert any("'toc'" in f for f in findings)


def test_overloaded_slide_flagged():
    from slide_ir import CalloutBlock, DiagramBlock, DiagramNode, StatBlock, StatItem

    slides = [
        SlideIR(
            slide_id="busy",
            layout_type=LayoutType.BULLET_EVIDENCE,
            title="x",
            blocks=[
                StatBlock(items=[StatItem(value="1")]),
                DiagramBlock(nodes=[DiagramNode(id="a", label="a")]),
                BulletBlock(items=["p"]),
                CalloutBlock(text="t"),
            ],
        ),
        # two heavy visuals stacked on a plain layout
        SlideIR(
            slide_id="heavy2",
            layout_type=LayoutType.BULLET_EVIDENCE,
            title="y",
            blocks=[
                DiagramBlock(nodes=[DiagramNode(id="a", label="a")]),
                TableBlock(columns=["c"], rows=[["1"]]),
            ],
        ),
        # a 2x2 grid page is NOT overloaded by design
        SlideIR(
            slide_id="grid",
            layout_type=LayoutType.FIGURE_GRID,
            title="g",
            blocks=[FigureBlock(asset_id="f1"), FigureBlock(asset_id="f2"), FigureBlock(asset_id="f3"), BulletBlock(items=["p"])],
        ),
    ]
    ev = [EvidenceAsset(asset_id=f"f{i}", kind="figure", content_ref="x.png", source="p.pdf") for i in (1, 2, 3)]
    findings = critique_deck(slides, ev)
    joined = " || ".join(findings)
    assert "slide 'busy'" in joined and "blocks on one slide" in joined
    assert "slide 'heavy2'" in joined and "heavy visual blocks" in joined
    assert "slide 'grid'" not in joined


def test_toc_section_mismatch_flagged():
    slides = [
        SlideIR(slide_id="t", layout_type=LayoutType.TOC, title="目录", blocks=[BulletBlock(items=["背景", "方法", "结果"])]),
        SlideIR(slide_id="s1", layout_type=LayoutType.SECTION, title="背景"),
        SlideIR(slide_id="c", layout_type=LayoutType.BULLET_EVIDENCE, title="x", blocks=[BulletBlock(items=["a", "b", "c", "d"])]),
    ]
    findings = critique_deck(slides, _EVIDENCE)
    assert any("3 个章节" in f and "1 个 section" in f for f in findings)
    # matched agenda -> clean
    slides += [
        SlideIR(slide_id="s2", layout_type=LayoutType.SECTION, title="方法"),
        SlideIR(slide_id="s3", layout_type=LayoutType.SECTION, title="结果"),
    ]
    assert not any("章节" in f for f in critique_deck(slides, _EVIDENCE))


def test_advisory_findings_do_not_burn_retries(tmp_path):
    # a deck whose ONLY finding is the [建议] monotony advisory must reach approval without replans
    slides = [
        {
            "slide_id": f"m{i}",
            "layout_type": "bullet_evidence",
            "title": f"页{i}",
            "blocks": [{"type": "bullets", "items": ["一", "二", "三", "→ 四"]}],
        }
        for i in range(5)
    ]
    deck = json.dumps({"deck_id": "j1", "slides": slides})
    graph = build_graph(FakeLLM(deck), out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "adv1"}}
    graph.invoke(_init(), cfg)
    snap = graph.get_state(cfg)
    assert "approval" in snap.next
    assert snap.values["retry_count"] == 0  # advisory surfaced but no replan burned
    assert any(f.startswith("[建议]") for f in snap.values["critic_findings"])
