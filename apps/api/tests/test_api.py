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
    assert body["ingested"] == 1


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
