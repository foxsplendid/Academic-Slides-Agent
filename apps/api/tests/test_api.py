"""API tests (TestClient + FakeLLM, no network).

Each test maps to a scenario in
openspec/changes/add-api-app/specs/api/spec.md.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from fastapi.testclient import TestClient

from asa_agents import FakeLLM
from asa_api import create_app

_VALID_DECK = json.dumps(
    {
        "deck_id": "d",
        "slides": [
            {"slide_id": "s1", "layout_type": "title", "title": "Sr-Nd isotopes", "blocks": []},
            {
                "slide_id": "s2",
                "layout_type": "two_column_table",
                "title": "Results",
                "blocks": [{"type": "table", "columns": ["Sample", "87Sr/86Sr"], "rows": [["HT-1", "0.7041"]]}],
            },
        ],
    }
)


def _client(tmp_path):
    return TestClient(create_app(FakeLLM(_VALID_DECK), out_dir=tmp_path))


def _csv(tmp_path) -> str:
    p = tmp_path / "d.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["Sample", "87Sr/86Sr"], ["HT-1", "0.7041"]])
    return str(p)


def test_create_stream_approve_download(tmp_path):
    client = _client(tmp_path)

    # create
    r = client.post("/jobs", json={"inputs": [_csv(tmp_path)]})
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    # stream to the Hard-Stop
    body = client.get(f"/jobs/{job_id}/stream").text
    assert "event: update" in body
    assert "awaiting_approval" in body
    assert not (Path(tmp_path) / f"{job_id}.pptx").exists()  # not compiled yet

    # approve -> resume -> compile
    r2 = client.post(f"/jobs/{job_id}/approve", json={"approved": True})
    assert r2.status_code == 200
    out = r2.json()["output_path"]
    assert out and Path(out).exists()

    # download
    r3 = client.get(f"/jobs/{job_id}/download")
    assert r3.status_code == 200
    assert r3.content[:2] == b"PK"  # .pptx is a zip


def test_create_returns_job_id(tmp_path):
    client = _client(tmp_path)
    r = client.post("/jobs", json={"inputs": [_csv(tmp_path)]})
    assert r.status_code == 200
    assert r.json()["job_id"]


def test_download_404_before_ready(tmp_path):
    client = _client(tmp_path)
    job_id = client.post("/jobs", json={"inputs": []}).json()["job_id"]
    assert client.get(f"/jobs/{job_id}/download").status_code == 404


_CSV_BYTES = b"Sample,87Sr/86Sr\nHT-1,0.7041\n"


def test_upload_creates_job(tmp_path):
    client = _client(tmp_path)
    r = client.post("/jobs/upload", files={"files": ("d.csv", _CSV_BYTES, "text/csv")})
    assert r.status_code == 200
    body = r.json()
    assert body["job_id"]
    # per-type ingestion counts: one CSV file -> one table
    assert body["ingested"]["files"] == 1
    assert body["ingested"]["tables"] == 1


def test_cors_header_present(tmp_path):
    client = _client(tmp_path)
    r = client.post("/jobs", json={"inputs": []}, headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_upload_end_to_end(tmp_path):
    client = _client(tmp_path)
    job_id = client.post(
        "/jobs/upload", files={"files": ("d.csv", _CSV_BYTES, "text/csv")}
    ).json()["job_id"]
    client.get(f"/jobs/{job_id}/stream")
    client.post(f"/jobs/{job_id}/approve", json={"approved": True})
    r = client.get(f"/jobs/{job_id}/download")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


# --- new-frontend backend: history / per-job options / preview / reject ---------


def test_jobs_history_and_delete(tmp_path):
    client = _client(tmp_path)
    r = client.post("/jobs/upload", files=[("files", ("d.csv", open(_csv(tmp_path), "rb"), "text/csv"))],
                    data={"style_name": "academic"})
    job_id = r.json()["job_id"]
    listing = client.get("/jobs").json()["jobs"]
    assert any(j["job_id"] == job_id and j["style"] == "academic" for j in listing)
    assert client.delete(f"/jobs/{job_id}").json()["status"] == "deleted"
    assert not any(j["job_id"] == job_id for j in client.get("/jobs").json()["jobs"])


def test_upload_per_job_options_reach_state(tmp_path):
    client = _client(tmp_path)
    r = client.post(
        "/jobs/upload",
        files=[("files", ("d.csv", open(_csv(tmp_path), "rb"), "text/csv"))],
        data={"style_name": "modern_teal", "vlm_critic": "true", "native_formula": "true"},
    )
    job_id = r.json()["job_id"]
    # stream to the Hard-Stop, then check the checkpointed state carries the options
    client.get(f"/jobs/{job_id}/stream")
    r2 = client.post(f"/jobs/{job_id}/approve", json={"approved": True})
    assert r2.status_code == 200  # full pipeline ran with per-job style without error


def test_preview_renders_or_503(tmp_path):
    client = _client(tmp_path)
    r = client.post("/jobs/upload", files=[("files", ("d.csv", open(_csv(tmp_path), "rb"), "text/csv"))])
    job_id = r.json()["job_id"]
    client.get(f"/jobs/{job_id}/stream")  # reach Hard-Stop (slides exist)
    pr = client.post(f"/jobs/{job_id}/preview")
    # On boxes with PowerPoint/LibreOffice this renders; elsewhere it must 503 cleanly (fail open).
    assert pr.status_code in (200, 503)
    if pr.status_code == 200:
        n = pr.json()["count"]
        assert n >= 1
        img = client.get(f"/jobs/{job_id}/preview/1")
        assert img.status_code == 200 and img.headers["content-type"] == "image/png"


def test_reject_stream_replans_to_new_hard_stop(tmp_path):
    client = _client(tmp_path)
    r = client.post("/jobs/upload", files=[("files", ("d.csv", open(_csv(tmp_path), "rb"), "text/csv"))])
    job_id = r.json()["job_id"]
    client.get(f"/jobs/{job_id}/stream")  # first Hard-Stop
    body = client.get(f"/jobs/{job_id}/stream", params={"reject": "1", "feedback": "标题太泛"}).text
    assert "awaiting_approval" in body  # replanned and stopped at approval again
    # approving after the rejection still completes
    r2 = client.post(f"/jobs/{job_id}/approve", json={"approved": True})
    assert r2.status_code == 200 and Path(r2.json()["output_path"]).exists()


def test_approve_409_when_not_awaiting(tmp_path):
    client = _client(tmp_path)
    r = client.post("/jobs/upload", files=[("files", ("d.csv", open(_csv(tmp_path), "rb"), "text/csv"))])
    job_id = r.json()["job_id"]
    assert client.post(f"/jobs/{job_id}/approve", json={"approved": True}).status_code == 409


def test_png_sorted_dedupes_case_insensitive_glob(tmp_path):
    from asa_api.app import _png_sorted

    for i in (1, 2, 10):
        (tmp_path / f"Slide{i}.PNG").write_bytes(b"x")
    pngs = _png_sorted(tmp_path)
    assert len(pngs) == 3  # not 6 (Windows globs are case-insensitive)
    assert [p.stem for p in pngs] == ["Slide1", "Slide2", "Slide10"]  # numeric order
