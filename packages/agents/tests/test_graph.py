"""Orchestration graph tests.

Each test maps to a scenario in
openspec/changes/add-langgraph-orchestration/specs/orchestration/spec.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from langgraph.types import Command

from slide_ir import EvidenceAsset, GenerationState, TableBlock
from asa_agents import FakeLLM
from asa_agents.graph import build_graph

_VALID_DECK = json.dumps(
    {
        "deck_id": "j1",
        "slides": [
            {"slide_id": "s1", "layout_type": "title", "title": "T", "blocks": []},
            {
                "slide_id": "s2",
                "layout_type": "bullet_evidence",
                "title": "M",
                "blocks": [{"type": "bullets", "items": ["a", "b"]}],
            },
        ],
    }
)


def _init() -> dict:
    return GenerationState(
        job_id="j1",
        evidence=[
            EvidenceAsset(asset_id="p1", kind="section_text", content_ref="text", source="paper.pdf", locator={})
        ],
        tables=[TableBlock(columns=["c"], rows=[["1"]])],
    ).model_dump()


def _field(result, name):
    return result.get(name) if isinstance(result, dict) else getattr(result, name, None)


def test_full_run_with_hard_stop_and_resume(tmp_path):
    graph = build_graph(FakeLLM(_VALID_DECK), out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "t1"}}

    graph.invoke(_init(), cfg)  # first run pauses at the approval interrupt
    assert list(Path(tmp_path).glob("*.pptx")) == []  # nothing compiled yet
    assert "approval" in graph.get_state(cfg).next

    final = graph.invoke(
        Command(resume={"approved": True, "edits": [{"slide_id": "s1", "title": "Edited"}]}), cfg
    )
    out = _field(final, "output_path")
    assert out and Path(out).exists()
    assert _field(final, "user_approved_outline") is True


def test_compile_writes_run_artifacts(tmp_path):
    from langgraph.types import Command

    graph = build_graph(FakeLLM(_VALID_DECK), out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "tr"}}
    graph.invoke(_init(), cfg)
    graph.invoke(Command(resume={"approved": True}), cfg)
    run_dir = Path(tmp_path) / "runs" / "j1"
    assert (run_dir / "out.pptx").exists()
    assert (run_dir / "deck.md").exists() and (run_dir / "deck.json").exists()
    assert "##" in (run_dir / "deck.md").read_text(encoding="utf-8")  # has slide headings


def test_streaming_emits_node_updates(tmp_path):
    graph = build_graph(FakeLLM(_VALID_DECK), out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "t2"}}
    updates = list(graph.stream(_init(), cfg, stream_mode="updates"))
    assert len(updates) >= 1
    keys = set()
    for update in updates:
        if isinstance(update, dict):
            keys |= set(update.keys())
    assert "plan" in keys


def test_non_ir_aborts_before_compile(tmp_path):
    graph = build_graph(FakeLLM("this is not slide-ir json"), out_dir=tmp_path)
    cfg = {"configurable": {"thread_id": "t3"}}
    with pytest.raises(Exception):
        graph.invoke(_init(), cfg)
    assert list(Path(tmp_path).glob("*.pptx")) == []
