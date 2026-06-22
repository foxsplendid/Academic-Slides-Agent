"""Headless CLI tests.

The LLM is mocked with ``FakeLLM`` exactly as the graph tests do (packages/agents/tests/test_graph.py)
— the deterministic compiler is the testable part. We assert the driver reaches the compiler and
writes a non-empty .pptx, and that the `outline` -> `build --from-outline` file-contract round-trip
resumes the same checkpointed run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from asa_agents import FakeLLM, build_outline

import asa_cli.__main__ as cli

_VALID_DECK = json.dumps(
    {
        "deck_id": "job",
        "slides": [
            {"slide_id": "s1", "layout_type": "title", "title": "Headless Deck", "blocks": []},
            {
                "slide_id": "s2",
                "layout_type": "bullet_evidence",
                "title": "Findings",
                "blocks": [{"type": "bullets", "items": ["a", "b"]}],
            },
        ],
    }
)


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    """Force build_cli_graph to use a scripted FakeLLM + the single-shot ``build_outline`` planner
    (so one scripted deck response drives the plan) + no formula sidecar — fast and offline,
    mirroring packages/agents/tests/test_graph.py."""
    real = cli.build_cli_graph

    def fake_build(*, out_dir, llm=None, formula_renderer=None, style=None, planner=None):
        return real(
            out_dir=out_dir,
            llm=FakeLLM(_VALID_DECK),
            formula_renderer=None,
            style=style,
            planner=build_outline,
        )

    monkeypatch.setattr(cli, "build_cli_graph", fake_build)


def _handoff_dir(tmp_path: Path) -> Path:
    d = tmp_path / "K0000001"
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(
        json.dumps(
            {
                "schema_version": "handoff/1.0",
                "key": "K0000001",
                "title": "Machine learning reconstruction of O2",
                "authors": ["Wang, A."],
                "year": "2024",
                "doi": "10.1000/xyz",
                "tldr": "ML reconstructs atmospheric oxygen.",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return d


def test_build_headless_writes_pptx(tmp_path):
    handoff = _handoff_dir(tmp_path)
    out_pptx = tmp_path / "deck.pptx"
    rc = cli.main(
        ["build", str(handoff), "--out", str(out_pptx), "--work-dir", str(tmp_path / "work")]
    )
    assert rc == 0
    assert out_pptx.exists() and out_pptx.stat().st_size > 0


def test_outline_then_from_outline_roundtrip(tmp_path):
    handoff = _handoff_dir(tmp_path)
    work = tmp_path / "work"
    outline_json = tmp_path / "outline.json"

    rc = cli.main(["outline", str(handoff), "--out", str(outline_json), "--work-dir", str(work)])
    assert rc == 0
    assert outline_json.exists()
    contract = json.loads(outline_json.read_text(encoding="utf-8"))
    assert contract["outline"], "outline contract should list slides"
    assert contract["job_id"] and contract["out_dir"]
    titles = [s["title"] for s in contract["outline"]]
    assert "Headless Deck" in titles  # the FakeLLM deck structure surfaced at the gate

    out_pptx = tmp_path / "resumed.pptx"
    rc2 = cli.main(["build", "--from-outline", str(outline_json), "--out", str(out_pptx)])
    assert rc2 == 0
    assert out_pptx.exists() and out_pptx.stat().st_size > 0


def test_from_outline_with_edits_resumes(tmp_path):
    """An edited outline contract (reviewer changed a title) resumes and still compiles."""
    handoff = _handoff_dir(tmp_path)
    work = tmp_path / "work"
    outline_json = tmp_path / "outline.json"
    cli.main(["outline", str(handoff), "--out", str(outline_json), "--work-dir", str(work)])

    contract = json.loads(outline_json.read_text(encoding="utf-8"))
    contract["edits"] = [{"slide_id": "s1", "title": "Reviewed Title"}]
    outline_json.write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")

    out_pptx = tmp_path / "edited.pptx"
    rc = cli.main(["build", "--from-outline", str(outline_json), "--out", str(out_pptx)])
    assert rc == 0
    assert out_pptx.exists() and out_pptx.stat().st_size > 0
