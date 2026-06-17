"""Unit tests for handoff-package ingestion.

Each test maps to a scenario in
openspec/changes/2026-06-17-add-handoff-ingestion/specs/ingestion/spec.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ingestion import ingest_handoff, ingest_path, is_handoff_dir


def _write_meta(dir_path: Path, meta: dict) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return dir_path


def _text_pdf(path: Path, text: str) -> None:
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure()
    fig.text(0.1, 0.5, text)
    fig.savefig(path)
    plt.close(fig)


# --- detection ---------------------------------------------------------------


def test_is_handoff_dir_true(tmp_path):
    d = _write_meta(tmp_path / "ABCD1234", {"schema_version": "handoff/1.0", "key": "ABCD1234", "title": "X"})
    assert is_handoff_dir(d) is True


def test_is_handoff_dir_false_for_plain_dir(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    assert is_handoff_dir(plain) is False
    # non-handoff meta.json is not a handoff package either
    _write_meta(tmp_path / "other", {"schema_version": "something/2"})
    assert is_handoff_dir(tmp_path / "other") is False


def test_router_dispatches_handoff_dir(tmp_path):
    d = _write_meta(
        tmp_path / "K0000001",
        {"schema_version": "handoff/1.0", "key": "K0000001", "title": "Atmospheric O2"},
    )
    res = ingest_path(d)
    assert any(a.asset_id == "report_basis" for a in res.assets)


def test_plain_directory_is_skipped(tmp_path):
    plain = tmp_path / "nothing"
    plain.mkdir()
    res = ingest_path(plain)  # must not raise
    assert res.assets == [] and res.tables == []


# --- single-paper (handoff/1.0) ----------------------------------------------


def test_single_paper_metadata_only(tmp_path):
    d = _write_meta(
        tmp_path / "K0000002",
        {
            "schema_version": "handoff/1.0",
            "key": "K0000002",
            "title": "Machine learning reconstruction of O2",
            "authors": ["Wang, A.", "Li, B."],
            "year": "2024",
            "doi": "10.1000/xyz123",
            "tldr": "ML reconstructs atmospheric oxygen.",
        },
    )
    res = ingest_handoff(d)
    basis = next(a for a in res.assets if a.asset_id == "report_basis")
    assert "本报告基于" in basis.content_ref
    assert "Machine learning reconstruction of O2" in basis.content_ref
    assert basis.locator["report_type"] == "literature"

    meta = next(a for a in res.assets if a.asset_id == "meta")
    assert "Wang, A." in meta.content_ref and "10.1000/xyz123" in meta.content_ref
    assert meta.locator["doi"] == "10.1000/xyz123" and meta.locator["year"] == "2024"


def test_single_paper_pdf_flows_through(tmp_path):
    d = tmp_path / "K0000003"
    d.mkdir()
    _text_pdf(d / "paper.pdf", "HelloHandoff")
    _write_meta(
        d,
        {"schema_version": "handoff/1.0", "key": "K0000003", "title": "T", "pdfFilename": "paper.pdf"},
    )
    res = ingest_handoff(d)
    texts = [a.content_ref for a in res.assets if a.kind == "section_text"]
    assert any("HelloHandoff" in t for t in texts)  # PDF text reached the pool


# --- multi-paper (handoff/1.1) -----------------------------------------------


def test_multi_paper_basis_and_unique_ids(tmp_path):
    d = _write_meta(
        tmp_path / "K0000004",
        {
            "schema_version": "handoff/1.1",
            "key": "K0000004",
            "report_type": "literature",
            "title": "Redox proxies — a synthesis",
            "papers": [
                {"title": "Paper One", "authors": ["Alpha"], "year": "2019", "doi": "10.1/a"},
                {"title": "Paper Two", "authors": ["Beta"], "year": "2021", "doi": "10.2/b"},
            ],
        },
    )
    res = ingest_handoff(d)
    basis = next(a for a in res.assets if a.asset_id == "report_basis")
    assert "Paper One" in basis.content_ref and "Paper Two" in basis.content_ref
    assert len(basis.locator["papers"]) == 2

    metas = [a.asset_id for a in res.assets if a.asset_id.endswith("meta")]
    assert set(metas) == {"p1_meta", "p2_meta"}  # namespaced, unique
    assert len({a.asset_id for a in res.assets}) == len(res.assets)  # no id collisions


def test_multi_paper_pdfs_namespaced(tmp_path):
    d = tmp_path / "K0000005"
    d.mkdir()
    # Same filename in nested folders would collide on the stem-derived ids without namespacing.
    (d / "one").mkdir()
    (d / "two").mkdir()
    _text_pdf(d / "one" / "paper.pdf", "FirstBody")
    _text_pdf(d / "two" / "paper.pdf", "SecondBody")
    _write_meta(
        d,
        {
            "schema_version": "handoff/1.1",
            "key": "K0000005",
            "title": "Two papers",
            "papers": [
                {"title": "One", "pdfFilename": "one/paper.pdf"},
                {"title": "Two", "pdfFilename": "two/paper.pdf"},
            ],
        },
    )
    res = ingest_handoff(d)
    assert len({a.asset_id for a in res.assets}) == len(res.assets)  # unique despite same filename
    assert any(a.asset_id.startswith("p1_") for a in res.assets)
    assert any(a.asset_id.startswith("p2_") for a in res.assets)


# --- report_type -------------------------------------------------------------


def test_report_type_defaults_to_literature(tmp_path):
    d = _write_meta(tmp_path / "K0000006", {"schema_version": "handoff/1.0", "key": "K0000006", "title": "T"})
    basis = next(a for a in ingest_handoff(d).assets if a.asset_id == "report_basis")
    assert basis.locator["report_type"] == "literature"


def test_report_type_experiment_recorded(tmp_path):
    d = _write_meta(
        tmp_path / "K0000007",
        {
            "schema_version": "handoff/1.1",
            "key": "K0000007",
            "report_type": "experiment",
            "title": "Run 42 results",
            "papers": [{"title": "Run 42"}, {"title": "Run 43"}],
        },
    )
    basis = next(a for a in ingest_handoff(d).assets if a.asset_id == "report_basis")
    assert basis.locator["report_type"] == "experiment"
    assert "实验报告" in basis.content_ref


# --- robustness --------------------------------------------------------------


def test_malformed_meta_warns_not_raises(tmp_path):
    d = tmp_path / "bad"
    d.mkdir()
    (d / "meta.json").write_text("{ not json", encoding="utf-8")
    res = ingest_handoff(d)  # must not raise
    assert res.assets == [] and res.warnings


def test_missing_pdf_warns(tmp_path):
    d = _write_meta(
        tmp_path / "K0000008",
        {"schema_version": "handoff/1.0", "key": "K0000008", "title": "T", "pdfFilename": "gone.pdf"},
    )
    res = ingest_handoff(d)
    assert any("缺少 PDF" in w for w in res.warnings)
    assert any(a.asset_id == "report_basis" for a in res.assets)  # still produced metadata evidence
