"""FastAPI service wrapping the orchestration graph.

Provider-agnostic: ``create_app`` takes an injected ``LLM`` (a ``FakeLLM`` in tests, a real
provider in production). Streaming is Server-Sent Events; the Hard-Stop is surfaced as an
``awaiting_approval`` event and resumed via ``POST /jobs/{id}/approve``.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel

from asa_agents.graph import build_graph
from ingestion import ingest
from slide_ir import GenerationState

_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class CreateJob(BaseModel):
    inputs: list[str] = []  # local file paths to ingest (self-hosted MVP)
    job_id: Optional[str] = None


class Approve(BaseModel):
    approved: bool = True
    edits: Optional[list[dict]] = None


def _get(obj, name, default=None):
    """Read a field from a dict or a model (LangGraph returns either shape)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _progress(update: dict) -> dict:
    out = {}
    for node, delta in update.items():
        phase = _get(delta, "phase")
        out[node] = {"phase": getattr(phase, "value", phase)}
    return out


def create_app(llm, *, formula_renderer=None, out_dir: str | Path = "exports", planner=None, style=None) -> FastAPI:
    app = FastAPI(title="Academic-Slides-Agent API")
    _origins = [
        o.strip()
        for o in os.environ.get(
            "ASA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    graph_kwargs = {"formula_renderer": formula_renderer, "out_dir": out_dir, "style": style}
    if planner is not None:
        graph_kwargs["planner"] = planner
    graph = build_graph(llm, **graph_kwargs)
    jobs: dict[str, dict] = {}

    def cfg(job_id: str) -> dict:
        return {"configurable": {"thread_id": job_id}}

    @app.post("/jobs")
    def create_job(req: CreateJob):
        job_id = req.job_id or uuid.uuid4().hex[:12]
        workspace = Path(out_dir) / "assets" / job_id
        cache = Path(out_dir) / "papers"  # shared content-addressed parse cache
        result = ingest(*req.inputs, workspace=workspace, cache_dir=cache) if req.inputs else None
        state = GenerationState(
            job_id=job_id,
            evidence=(result.assets if result else []),
            tables=(result.tables if result else []),
        )
        jobs[job_id] = state.model_dump()
        return {"job_id": job_id, "status": "created"}

    @app.post("/jobs/upload")
    async def create_job_upload(files: list[UploadFile] = File(default=[])):
        job_id = uuid.uuid4().hex[:12]
        job_dir = Path(out_dir) / "uploads" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        for upload in files:
            dest = job_dir / (upload.filename or "upload.bin")
            dest.write_bytes(await upload.read())
            paths.append(str(dest))
        cache = Path(out_dir) / "papers"  # shared content-addressed parse cache (dedup re-uploads)
        result = ingest(*paths, workspace=job_dir, cache_dir=cache) if paths else None
        assets = result.assets if result else []
        state = GenerationState(
            job_id=job_id,
            evidence=assets,
            tables=(result.tables if result else []),
        )
        jobs[job_id] = state.model_dump()
        return {
            "job_id": job_id,
            "status": "created",
            "ingested": {
                "files": len(paths),
                "tables": len(result.tables) if result else 0,
                "figures": sum(1 for a in assets if a.kind == "figure"),
                "text_pages": sum(1 for a in assets if a.kind == "section_text"),
            },
            "warnings": (result.warnings if result else []),
        }

    @app.get("/jobs/{job_id}/stream")
    def stream(job_id: str):
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="job not found")
        initial = jobs[job_id]

        def gen():
            # ["updates","custom"] yields (mode, chunk): node deltas + per-slide progress events.
            for mode, chunk in graph.stream(initial, cfg(job_id), stream_mode=["updates", "custom"]):
                if mode == "custom":
                    yield _sse("progress", chunk.get("progress", chunk) if isinstance(chunk, dict) else {})
                elif mode == "updates" and isinstance(chunk, dict) and "__interrupt__" not in chunk:
                    yield _sse("update", _progress(chunk))
            snap = graph.get_state(cfg(job_id))
            if "approval" in (snap.next or ()):
                yield _sse("awaiting_approval", {"outline": _get(snap.values, "outline")})
            else:
                yield _sse("done", {"output_path": _get(snap.values, "output_path")})

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/jobs/{job_id}/approve")
    def approve(job_id: str, req: Approve):
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="job not found")
        final = graph.invoke(
            Command(resume={"approved": req.approved, "edits": req.edits}), cfg(job_id)
        )
        return {"job_id": job_id, "status": "done", "output_path": _get(final, "output_path")}

    @app.get("/jobs/{job_id}/download")
    def download(job_id: str):
        snap = graph.get_state(cfg(job_id))
        out = _get(snap.values, "output_path")
        if not out or not Path(out).exists():
            raise HTTPException(status_code=404, detail="deck not ready")
        return FileResponse(out, filename=f"{job_id}.pptx", media_type=_PPTX_MIME)

    return app
