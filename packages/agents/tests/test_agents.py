"""Unit tests for the outline agent.

Each test maps to a scenario in
openspec/changes/add-outline-agent/specs/outline-agent/spec.md.
"""

from __future__ import annotations

import json

import pytest

from slide_ir import EvidenceAsset, GenerationState, IRBoundaryError, Phase, TableBlock
from asa_agents import FakeLLM, approve_outline, build_outline, plan_outline


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
