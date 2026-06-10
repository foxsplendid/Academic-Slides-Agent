"""Unit tests for the outline agent.

Each test maps to a scenario in
openspec/changes/add-outline-agent/specs/outline-agent/spec.md.
"""

from __future__ import annotations

import json
import re
import threading

import pytest

from slide_ir import EvidenceAsset, GenerationState, IRBoundaryError, LayoutType, Phase, SlideIR, TableBlock
from asa_agents import FakeLLM, approve_outline, build_deck_detailed, build_outline, plan_outline


def _evidence():
    assets = [
        EvidenceAsset(
            asset_id="p1",
            kind="section_text",
            content_ref="We measured Sr-Nd isotopes of the Hart suite.",
            source="paper.pdf",
            locator={"page": 1},
        )
    ]
    tables = [TableBlock(columns=["Sample", "87Sr/86Sr"], rows=[["HT-1", "0.7041"]], caption="t")]
    return assets, tables


_VALID_DECK = json.dumps(
    {
        "deck_id": "d1",
        "slides": [
            {
                "slide_id": "s1",
                "layout_type": "title",
                "title": "Sr-Nd isotopes",
                "blocks": [],
                "provenance": {"source": "paper.pdf"},
            },
            {
                "slide_id": "s2",
                "layout_type": "two_column_table",
                "title": "Results",
                "blocks": [{"type": "table", "columns": ["Sample", "87Sr/86Sr"], "rows": [["HT-1", "0.7041"]]}],
                "provenance": {"source": "paper.pdf"},
            },
        ],
    }
)


def test_valid_ir_returns_deck():
    assets, tables = _evidence()
    deck = build_outline(assets, tables, FakeLLM(_VALID_DECK))
    assert deck.deck_id == "d1"
    assert len(deck.slides) == 2


def test_non_ir_output_rejected():
    assets, tables = _evidence()
    with pytest.raises(IRBoundaryError):
        build_outline(assets, tables, FakeLLM("Sure! Here is your deck: <html>..."))


def test_prompt_carries_evidence_and_system():
    assets, tables = _evidence()
    llm = FakeLLM(_VALID_DECK)
    build_outline(assets, tables, llm)
    call = llm.calls[0]
    assert "isotopes" in call["prompt"].lower() or "87Sr" in call["prompt"]
    assert call["system"] and "组会" in call["system"]


def test_plan_outline_pauses_at_hard_stop():
    assets, tables = _evidence()
    state = GenerationState(job_id="j1")
    plan_outline(state, assets, tables, FakeLLM(_VALID_DECK))
    assert state.phase is Phase.AWAIT_OUTLINE_APPROVAL
    assert len(state.slides) == 2
    assert state.outline and state.outline[0]["title"] == "Sr-Nd isotopes"
    assert state.user_approved_outline is False


def test_approve_outline_advances():
    state = GenerationState(job_id="j1", phase=Phase.AWAIT_OUTLINE_APPROVAL)
    approve_outline(state, edited_outline=[{"slide_id": "s1", "title": "Edited"}])
    assert state.user_approved_outline is True
    assert state.phase is Phase.MAPPING
    assert state.user_outline_edits[0]["title"] == "Edited"


def test_fake_llm_records_and_scripts():
    llm = FakeLLM("a", "b")
    assert llm.complete("x") == "a"
    assert llm.complete("y") == "b"
    assert llm.complete("z") == "b"  # repeats the last
    assert len(llm.calls) == 3


def test_build_outline_accepts_fenced_json():
    assets, tables = _evidence()
    fenced = "Here is your deck:\n```json\n" + _VALID_DECK + "\n```\n"
    deck = build_outline(assets, tables, FakeLLM(fenced))
    assert deck.deck_id == "d1"
    assert len(deck.slides) == 2


def test_prompt_lists_available_figure_ids():
    from asa_agents.outline import build_outline_prompt

    assets, tables = _evidence()  # no figure assets
    assert "(无" in build_outline_prompt(assets, tables)  # tells the model: no figures

    with_fig = assets + [
        EvidenceAsset(asset_id="fig1", kind="figure", content_ref="f.png", source="paper.pdf")
    ]
    assert "fig1" in build_outline_prompt(with_fig, tables)


def test_ir_boundary_retry_recovers():
    assets, tables = _evidence()
    # first response is malformed, second is valid -> build_outline recovers
    llm = FakeLLM("oops not json", _VALID_DECK)
    deck = build_outline(assets, tables, llm)
    assert deck.deck_id == "d1"
    assert len(llm.calls) == 2  # retried once after the boundary error
    assert "不符合 schema" in llm.calls[1]["prompt"]  # error fed back


def test_ir_boundary_retry_exhausts_and_raises():
    assets, tables = _evidence()
    llm = FakeLLM("never valid ir")  # repeats; never parses
    with pytest.raises(IRBoundaryError):
        build_outline(assets, tables, llm, max_attempts=3)
    assert len(llm.calls) == 3  # tried the full budget


def test_valid_deck_parses_on_first_attempt():
    assets, tables = _evidence()
    llm = FakeLLM(_VALID_DECK)
    build_outline(assets, tables, llm)
    assert len(llm.calls) == 1  # no extra calls when the first response is valid


# --- add-detailed-slide-content: two-stage builder ---------------------------

_SKELETON = json.dumps(
    {
        "slides": [
            {"slide_id": "s1", "layout_type": "title", "title": "Sr-Nd 同位素", "focus": "一句话", "evidence_pages": [], "figure_id": None},
            {"slide_id": "s2", "layout_type": "bullet_evidence", "title": "结果", "focus": "讲清结果", "evidence_pages": [1], "figure_id": None},
        ]
    }
)
_SLIDE1 = json.dumps(
    {"slide_id": "s1", "layout_type": "title", "title": "Sr-Nd 同位素", "blocks": [], "speaker_notes": "开场", "provenance": {"source": "p1"}}
)
_SLIDE2 = json.dumps(
    {
        "slide_id": "s2",
        "layout_type": "bullet_evidence",
        "title": "结果",
        "blocks": [{"type": "bullets", "items": ["细节A具体方法", "数值 0.7041", "机制解释", "→ 这说明了什么"]}],
        "speaker_notes": "这一页讲结果细节,照着念。",
        "provenance": {"source": "p1"},
    }
)


def test_two_stage_builder_deepens_content():
    from asa_agents import build_deck_detailed

    assets, tables = _evidence()
    # 1 skeleton call + 1 call per slide (2 slides)
    llm = FakeLLM(_SKELETON, _SLIDE1, _SLIDE2)
    deck = build_deck_detailed(assets, tables, llm)
    assert len(deck.slides) == 2
    assert len(llm.calls) == 3  # skeleton + 2 expansions
    s2 = deck.slides[1]
    assert s2.blocks and s2.blocks[0].type == "bullets"
    assert len(s2.blocks[0].items) >= 4  # deeper than single-shot
    assert s2.speaker_notes  # notes generated


def test_incremental_repair_only_recalls_flagged_slide():
    from slide_ir import BulletBlock, LayoutType, SlideIR

    prior = [
        SlideIR(slide_id="s1", layout_type=LayoutType.BULLET_EVIDENCE, title="good", blocks=[BulletBlock(items=["a", "b"])], speaker_notes="n"),
        SlideIR(slide_id="s2", layout_type=LayoutType.BULLET_EVIDENCE, title="bad", blocks=[BulletBlock(items=["x"])], speaker_notes="n"),
    ]
    feedback = ["slide 's2': bullet list too long (9 > 7 items)"]
    fixed = json.dumps(
        {"slide_id": "s2", "layout_type": "bullet_evidence", "title": "fixed", "blocks": [{"type": "bullets", "items": ["short"]}], "speaker_notes": "n", "provenance": {"source": "p"}}
    )
    llm = FakeLLM(fixed)
    deck = build_deck_detailed([], [], llm, feedback=feedback, prior_slides=prior)
    assert len(llm.calls) == 1  # only the flagged slide was re-generated (no skeleton, no good-slide calls)
    assert deck.slides[0].title == "good"  # unflagged slide kept verbatim
    assert deck.slides[1].title == "fixed"  # flagged slide repaired


def test_two_stage_keeps_assigned_figure():
    from asa_agents import build_deck_detailed

    assets = [
        EvidenceAsset(asset_id="p1", kind="section_text", content_ref="text", source="paper.pdf", locator={"page": 1}),
        EvidenceAsset(asset_id="fig1", kind="figure", content_ref="f.png", source="paper.pdf", locator={"page": 1, "caption": "Fig.1"}),
    ]
    skeleton = json.dumps(
        {"slides": [{"slide_id": "s1", "layout_type": "figure_caption", "title": "图", "focus": "看图", "evidence_pages": [1], "figure_id": "fig1"}]}
    )
    slide = json.dumps(
        {"slide_id": "s1", "layout_type": "figure_caption", "title": "图", "blocks": [{"type": "figure", "asset_id": "fig1", "caption": "Fig.1"}], "speaker_notes": "看图", "provenance": {"source": "p1"}}
    )
    deck = build_deck_detailed(assets, [], FakeLLM(skeleton, slide))
    figs = [b for s in deck.slides for b in s.blocks if b.type == "figure"]
    assert figs and figs[0].asset_id == "fig1"


# --- add-parallel-progress: parallel expansion + progress --------------------


def _plans(n):
    return [
        {"slide_id": f"s{i}", "layout_type": "bullet_evidence", "title": f"页{i}", "focus": "f", "evidence_pages": [], "figure_id": None}
        for i in range(n)
    ]


def _slide_json(title):
    return json.dumps(
        {"title": title, "blocks": [{"type": "bullets", "items": ["a", "b", "c", "d"]}], "speaker_notes": "n", "provenance": {"source": "p"}}
    )


class _EchoLLM:
    """Skeleton, then echo each slide's title from the prompt — order-independent & thread-safe."""

    def __init__(self, skeleton):
        self.skeleton = skeleton
        self._lock = threading.Lock()

    def complete(self, prompt, *, system=None):
        with self._lock:
            pass
        if system and "一页" in system:  # expansion call
            m = re.search(r"页标题:(.+)", prompt)
            return _slide_json(m.group(1).strip() if m else "X")
        return self.skeleton


def test_parallel_preserves_order_and_reports_progress():
    assets, tables = _evidence()
    llm = _EchoLLM(json.dumps({"slides": _plans(5)}))
    events: list[dict] = []
    deck = build_deck_detailed(assets, tables, llm, progress=events.append)
    assert [s.title for s in deck.slides] == [f"页{i}" for i in range(5)]  # order preserved
    slide_events = [e for e in events if e.get("phase") == "slide"]
    assert slide_events[-1]["done"] == 5 and slide_events[-1]["total"] == 5


class _WorkerFailLLM:
    """Expansion fails on worker threads (forces the serial fallback) but works on the main thread."""

    def __init__(self, skeleton):
        self.skeleton = skeleton

    def complete(self, prompt, *, system=None):
        if system and "一页" in system:
            if threading.current_thread() is not threading.main_thread():
                raise RuntimeError("parallel boom")
            m = re.search(r"页标题:(.+)", prompt)
            return _slide_json(m.group(1).strip() if m else "X")
        return self.skeleton


def test_serial_fallback_on_worker_failure():
    assets, tables = _evidence()
    llm = _WorkerFailLLM(json.dumps({"slides": _plans(3)}))
    events: list[dict] = []
    deck = build_deck_detailed(assets, tables, llm, progress=events.append)
    assert len(deck.slides) == 3  # serial fallback produced the full deck
    assert any(e.get("phase") == "fallback_serial" for e in events)


# --- add-supplementary-inputs: tables reach expansion ------------------------


def test_serialize_table_caps_rows():
    from asa_agents.outline import serialize_table

    tb = TableBlock(columns=["i"], rows=[[str(n)] for n in range(500)])
    s = serialize_table(tb, max_rows=10, max_chars=100000)
    assert "还有 490 行" in s
    assert s.count("\n") <= 12  # header + 10 rows + remainder note


def test_expand_receives_referenced_table_data():
    from asa_agents.deepen import _expand_slide

    tables = [TableBlock(columns=["el", "shap"], rows=[["Mo", "0.42"], ["Fe", "0.18"]])]
    captured: dict[str, str] = {}

    class _Cap:
        def complete(self, prompt, *, system=None):
            captured["p"] = prompt
            return json.dumps(
                {"title": "t", "blocks": [{"type": "bullets", "items": ["a", "b"]}], "speaker_notes": "n", "provenance": {"source": "p"}}
            )

    plan = {"slide_id": "s1", "layout_type": "bullet_evidence", "title": "t", "focus": "f", "evidence_pages": [], "table_refs": [0]}
    _expand_slide(plan, {}, {}, _Cap(), tables)
    assert "Mo" in captured["p"] and "0.42" in captured["p"]  # the table data reached the prompt


# --- add-parse-cache: deck markdown ------------------------------------------


def test_deck_to_markdown_renders():
    from asa_agents import deck_to_markdown
    from slide_ir import BulletBlock, Deck, LayoutType, SlideIR

    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s1",
                layout_type=LayoutType.BULLET_EVIDENCE,
                title="标题",
                blocks=[BulletBlock(items=["a", "b"])],
                speaker_notes="讲一下",
            )
        ],
    )
    md = deck_to_markdown(deck)
    assert "## 1. 标题" in md and "- a" in md and "讲稿: 讲一下" in md


def test_deck_to_markdown_renders_diagram():
    from asa_agents import deck_to_markdown
    from slide_ir import Deck, DiagramBlock, DiagramNode, LayoutType, SlideIR

    deck = Deck(
        deck_id="d",
        slides=[
            SlideIR(
                slide_id="s1",
                layout_type=LayoutType.BULLET_EVIDENCE,
                title="流程",
                blocks=[DiagramBlock(diagram_type="flow", nodes=[DiagramNode(id="a", label="第一步"), DiagramNode(id="b", label="第二步")])],
            )
        ],
    )
    md = deck_to_markdown(deck)
    assert "[diagram: flow]" in md and "第一步" in md


# --- speedup: adaptive evidence cap + env-tunable concurrency ----------------


class _CaptureLLM:
    def __init__(self):
        self.prompt = ""

    def complete(self, prompt, *, system=None):
        self.prompt = prompt
        return _slide_json("X")


def test_expand_evidence_cap_adaptive():
    from asa_agents.deepen import _expand_slide

    ev = {1: "字" * 20000}
    plain = {"slide_id": "s", "layout_type": "bullet_evidence", "title": "t", "focus": "f", "evidence_pages": [1]}
    llm = _CaptureLLM()
    _expand_slide(plain, ev, {}, llm)
    assert llm.prompt.count("字") <= 6050  # plain bullet slide -> tighter cap

    fig = {**plain, "figure_id": "x"}
    _expand_slide(fig, ev, {"x": "caption"}, llm)
    assert 6050 < llm.prompt.count("字") <= 9050  # figure slide keeps full context


def test_expand_workers_env_limits_concurrency(monkeypatch):
    import time as _t

    monkeypatch.setenv("ASA_EXPAND_WORKERS", "2")
    lock = threading.Lock()
    cur = {"n": 0, "peak": 0}

    class _ConcLLM:
        def __init__(self, skeleton):
            self.skeleton = skeleton

        def complete(self, prompt, *, system=None):
            if system and "一页" in system:
                with lock:
                    cur["n"] += 1
                    cur["peak"] = max(cur["peak"], cur["n"])
                _t.sleep(0.05)
                with lock:
                    cur["n"] -= 1
                m = re.search(r"页标题:(.+)", prompt)
                return _slide_json(m.group(1).strip() if m else "X")
            return self.skeleton

    assets, tables = _evidence()
    build_deck_detailed(assets, tables, _ConcLLM(json.dumps({"slides": _plans(6)})))
    assert cur["peak"] <= 2  # ASA_EXPAND_WORKERS=2 capped in-flight expansions


# --- dedup + layout backstop -------------------------------------------------


def test_skeleton_dedup_drops_near_duplicate():
    from asa_agents.deepen import _dedup_plans

    plans = [
        {"slide_id": "s0", "title": "质量与数量阈值的权衡", "focus": "讲阈值权衡", "layout_type": "bullet_evidence", "evidence_pages": []},
        {"slide_id": "s1", "title": "研究背景", "focus": "背景", "layout_type": "bullet_evidence", "evidence_pages": []},
        {"slide_id": "s2", "title": "质量数量阈值权衡", "focus": "讲阈值权衡", "layout_type": "bullet_evidence", "evidence_pages": []},
    ]
    kept = _dedup_plans(plans)
    assert [p["slide_id"] for p in kept] == ["s0", "s1"]  # near-dup s2 dropped, order preserved


def test_dedup_keeps_distinct():
    from asa_agents.deepen import _dedup_plans

    plans = [
        {"title": "数据与方法", "focus": "a"},
        {"title": "结果与验证", "focus": "b"},
        {"title": "讨论与机制", "focus": "c"},
    ]
    assert len(_dedup_plans(plans)) == 3


def test_dedup_not_expanded():
    """A dropped near-duplicate plan is never expanded (saves an LLM call)."""
    skeleton = json.dumps(
        {"slides": [
            {"slide_id": "s0", "title": "阈值权衡分析", "focus": "f", "layout_type": "bullet_evidence", "evidence_pages": []},
            {"slide_id": "s1", "title": "阈值权衡的分析", "focus": "f", "layout_type": "bullet_evidence", "evidence_pages": []},
        ]}
    )
    assets, tables = _evidence()
    deck = build_deck_detailed(assets, tables, _EchoLLM(skeleton))
    assert len(deck.slides) == 1  # the two near-dup plans collapsed to one


def test_structural_layout_relayout_at_assembly():
    from asa_agents.deepen import _fix_structural_layout

    s = SlideIR.model_validate(
        {"slide_id": "x", "layout_type": "section", "title": "结果", "blocks": [{"type": "bullets", "items": ["a"]}], "speaker_notes": "n", "provenance": {"source": "p"}}
    )
    assert _fix_structural_layout(s).layout_type == LayoutType.BULLET_EVIDENCE

    divider = SlideIR.model_validate(
        {"slide_id": "y", "layout_type": "section", "title": "方法", "blocks": [], "speaker_notes": "", "provenance": {"source": "p"}}
    )
    assert _fix_structural_layout(divider).layout_type == LayoutType.SECTION  # real divider untouched


def test_figure_menu_carries_captions_and_warns_uncaptioned():
    from asa_agents.outline import figure_menu

    assets = [
        EvidenceAsset(asset_id="f1", kind="figure", content_ref="a.png", source="p.pdf", locator={"caption": "Fig. 1. Workflow of the ML method"}),
        EvidenceAsset(asset_id="f2", kind="figure", content_ref="b.png", source="p.pdf", locator={"caption": ""}),
    ]
    menu = figure_menu(assets)
    assert "Fig. 1. Workflow" in menu  # caption hint present
    assert "慎用" in menu  # captionless figure flagged


# --- P1: detail-level density contracts ----------------------------------------


def test_detail_level_reaches_prompts():
    assets, tables = _evidence()
    llm = _EchoLLM(json.dumps({"slides": _plans(2)}))
    captured = []
    orig = llm.complete

    def spy(prompt, *, system=None):
        captured.append(prompt)
        return orig(prompt, system=system)

    llm.complete = spy
    build_deck_detailed(assets, tables, llm, detail="high", parallel=False)
    assert any("12-15" in p for p in captured)  # skeleton got the content-page budget
    assert any("5-7" in p for p in captured)  # expansions got the bullet quota


def test_unknown_detail_falls_back_to_auto():
    from asa_agents.deepen import _detail_profile

    assert _detail_profile("nonsense") is None  # auto: model-decided density
    assert _detail_profile("auto") is None
    assert _detail_profile("high") is not None  # explicit levels remain available


def test_table_title_normalized_to_caption():
    from asa_agents.deepen import _normalize_blocks

    d = {"blocks": [{"type": "table", "title": "主要端元特征", "columns": ["a"], "rows": []}]}
    out = _normalize_blocks(d)
    b = out["blocks"][0]
    assert "title" not in b and b["caption"] == "主要端元特征"


# --- add-visual-canvas: premium tier -----------------------------------------

_CANVAS_OK_SVG = (
    '<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 1280 720\\">'
    '<text x=\\"90\\" y=\\"80\\" font-size=\\"30\\" fill=\\"#333333\\">机制图</text></svg>'
)
_CANVAS_PLAN = json.dumps(
    {"slides": [{"slide_id": "s1", "layout_type": "canvas", "title": "机制", "focus": "画", "evidence_pages": [1], "figure_ids": [], "table_refs": []}]}
)
_CANVAS_SLIDE = (
    '{"slide_id":"s1","layout_type":"canvas","title":"机制","blocks":[{"type":"canvas","svg":"'
    + _CANVAS_OK_SVG
    + '"}],"speaker_notes":"n","provenance":{"source":"p1"}}'
)


def test_premium_adds_canvas_vocabulary_to_skeleton():
    from asa_agents.deepen import PREMIUM_SKELETON_NOTE, build_deck_detailed

    assets, tables = _evidence()
    llm = FakeLLM(_CANVAS_PLAN, _CANVAS_SLIDE)
    build_deck_detailed(assets, tables, llm, premium=True)
    assert any("canvas" in (c["system"] or "") for c in llm.calls)  # note injected
    llm2 = FakeLLM(_SKELETON, _SLIDE1, _SLIDE2)
    build_deck_detailed(assets, tables, llm2, premium=False)
    assert not any("PREMIUM" in (c["system"] or "") or "自由构图" in (c["system"] or "") for c in llm2.calls[:1])


def test_canvas_plan_routes_to_canvas_prompt_and_validates():
    from asa_agents.deepen import build_deck_detailed

    assets, tables = _evidence()
    llm = FakeLLM(_CANVAS_PLAN, _CANVAS_SLIDE)
    deck = build_deck_detailed(assets, tables, llm, premium=True)
    assert deck.slides[0].layout_type.value == "canvas"
    assert deck.slides[0].blocks[0].type == "canvas"
    # the expansion call used the canvas authoring system prompt
    assert any("自由构图" in (c["system"] or "") for c in llm.calls)


def test_invalid_canvas_retries_then_falls_back_to_bullets():
    from asa_agents.deepen import build_deck_detailed

    bad = _CANVAS_SLIDE.replace("</text>", "</text><script>x</script>")
    bullets = json.dumps(
        {"slide_id": "s1", "layout_type": "bullet_evidence", "title": "机制", "blocks": [{"type": "bullets", "items": ["a", "b", "→ ok"]}], "speaker_notes": "n", "provenance": {"source": "p1"}}
    )
    assets, tables = _evidence()
    # skeleton, then 3 canvas attempts (all invalid), then the bullet fallback expansion succeeds
    llm = FakeLLM(_CANVAS_PLAN, bad, bad, bad, bullets)
    deck = build_deck_detailed(assets, tables, llm, premium=True)
    assert deck.slides[0].layout_type.value == "bullet_evidence"  # degraded, run not killed


def test_rejection_feedback_triggers_full_replan():
    from slide_ir import BulletBlock, LayoutType, SlideIR

    prior = [
        SlideIR(slide_id="s1", layout_type=LayoutType.BULLET_EVIDENCE, title="旧页", blocks=[BulletBlock(items=["a", "b", "c"])], speaker_notes="n"),
    ]
    assets, tables = _evidence()
    llm = FakeLLM(_SKELETON, _SLIDE1, _SLIDE2)
    deck = build_deck_detailed(assets, tables, llm, feedback=["用户退回大纲: 结构太散,按方法-结果重组"], prior_slides=prior)
    # a full replan ran: skeleton + expansions, NOT a no-op patch of prior slides
    assert len(llm.calls) == 3
    assert "用户退回大纲" in llm.calls[0]["prompt"]
    assert "上一稿大纲" in llm.calls[0]["prompt"]  # prior outline handed over as context
    assert [s.title for s in deck.slides] != ["旧页"]


def test_canvas_expansion_injects_matching_exemplar():
    plan_with_keywords = json.dumps(
        {"slides": [{"slide_id": "s1", "layout_type": "canvas", "title": "预测与观测相关性", "focus": "散点与对角线", "evidence_pages": [1], "figure_ids": [], "table_refs": []}]}
    )
    assets, tables = _evidence()
    llm = FakeLLM(plan_with_keywords, _CANVAS_SLIDE)
    build_deck_detailed(assets, tables, llm, premium=True)
    canvas_call = next(c for c in llm.calls if "整页 SVG" in (c["system"] or ""))
    assert "构图范例" in canvas_call["prompt"] and "scatter_chart" in canvas_call["prompt"]
