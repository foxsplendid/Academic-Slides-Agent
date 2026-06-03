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
    assert call["system"] and "academic" in call["system"].lower()


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
