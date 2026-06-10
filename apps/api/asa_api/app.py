"""FastAPI service wrapping the orchestration graph.

Provider-agnostic: ``create_app`` takes an injected ``LLM`` (a ``FakeLLM`` in tests, a real
provider in production). Streaming is Server-Sent Events; the Hard-Stop is surfaced as an
``awaiting_approval`` event and resumed via ``POST /jobs/{id}/approve`` (or, for a rejection with
feedback, by re-opening the stream with ``?reject=1`` so the replan progress streams live).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
import uuid
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel

from asa_agents.graph import build_graph
from ingestion import ingest
from slide_ir import Deck, GenerationState

_PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class CreateJob(BaseModel):
    inputs: list[str] = []  # local file paths to ingest (self-hosted MVP)
    job_id: Optional[str] = None


class Approve(BaseModel):
    approved: bool = True
    edits: Optional[list[dict]] = None
    feedback: Optional[str] = None


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


@contextmanager
def _env_overrides(overrides: dict[str, Optional[str]]):
    """Temporarily apply env values (ingestion reads its toggles from env). Local single-process
    server — the window is the synchronous ingest call inside the request."""
    old: dict[str, Optional[str]] = {}
    for k, v in overrides.items():
        if v is None or v == "":
            continue
        old[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        yield
    finally:
        for k, prev in old.items():
            if prev is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = prev


def _png_sorted(folder: Path) -> list[Path]:
    # Dedupe by name: Windows globbing is case-insensitive, so *.png + *.PNG would list every
    # frame twice (the "every slide shows twice" bug).
    uniq = {p.name.lower(): p for p in list(folder.glob("*.png")) + list(folder.glob("*.PNG"))}
    pngs = list(uniq.values())
    pngs.sort(key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    return pngs


class _JobRun:
    """An in-memory, replayable event log for one background graph run. The SSE endpoint tails it,
    so client disconnects never abort generation and reconnects replay from the start."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []
        self.done = False
        self.cond = threading.Condition()

    def emit(self, event: str, data: dict) -> None:
        with self.cond:
            self.events.append((event, data))
            self.cond.notify_all()

    def finish(self) -> None:
        with self.cond:
            self.done = True
            self.cond.notify_all()


def _tail(run: _JobRun):
    """Yield SSE frames from a run's event log: replay history, follow live, heartbeat when idle."""
    idx = 0
    while True:
        with run.cond:
            if idx >= len(run.events) and not run.done:
                run.cond.wait(timeout=10.0)
            has = idx < len(run.events)
            done = run.done
        if has:
            event, data = run.events[idx]
            idx += 1
            yield _sse(event, data)
        elif done:
            return
        else:
            yield ": keepalive\n\n"  # SSE comment — defeats idle-connection timeouts


def create_app(
    llm,
    *,
    formula_renderer=None,
    out_dir: str | Path = "exports",
    planner=None,
    style=None,
    vision_llm=None,
    checkpointer=None,
    icon_renderer=None,
) -> FastAPI:
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
    graph_kwargs = {
        "formula_renderer": formula_renderer,
        "out_dir": out_dir,
        "style": style,
        "vision_llm": vision_llm,
        "checkpointer": checkpointer,
        "icon_renderer": icon_renderer,
    }
    if planner is not None:
        graph_kwargs["planner"] = planner
    graph = build_graph(llm, **graph_kwargs)
    jobs: dict[str, dict] = {}
    out_root = Path(out_dir)
    meta_dir = out_root / "meta"
    states_dir = out_root / "states"  # persisted initial states: jobs survive a restart pre-stream too
    preview_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)  # serialize per-job renders
    active_runs: dict[str, _JobRun] = {}

    def _save_state(job_id: str, state: GenerationState) -> None:
        try:
            states_dir.mkdir(parents=True, exist_ok=True)
            (states_dir / f"{job_id}.json").write_text(state.model_dump_json(), encoding="utf-8")
        except Exception:
            pass

    def _load_state(job_id: str) -> Optional[dict]:
        try:
            return json.loads((states_dir / f"{job_id}.json").read_text(encoding="utf-8"))
        except Exception:
            return None

    def _execute(job_id: str, run: _JobRun, stream_input) -> None:
        try:
            for mode, chunk in graph.stream(stream_input, cfg(job_id), stream_mode=["updates", "custom"]):
                if mode == "custom":
                    run.emit("progress", chunk.get("progress", chunk) if isinstance(chunk, dict) else {})
                elif mode == "updates" and isinstance(chunk, dict) and "__interrupt__" not in chunk:
                    run.emit("update", _progress(chunk))
            snap = graph.get_state(cfg(job_id))
            if "approval" in (snap.next or ()):
                run.emit("awaiting_approval", {"outline": _get(snap.values, "outline")})
            else:
                run.emit("done", {"output_path": _get(snap.values, "output_path")})
        except Exception as err:  # surface the real reason instead of a silent connection drop
            run.emit("error", {"message": str(err)[:300]})
        finally:
            run.finish()

    def _start_run(job_id: str, stream_input) -> _JobRun:
        run = _JobRun()
        active_runs[job_id] = run
        threading.Thread(target=_execute, args=(job_id, run, stream_input), daemon=True).start()
        return run

    def cfg(job_id: str) -> dict:
        return {"configurable": {"thread_id": job_id}}

    def _write_meta(job_id: str, title: str, job_style: str, options: dict) -> None:
        try:
            meta_dir.mkdir(parents=True, exist_ok=True)
            (meta_dir / f"{job_id}.json").write_text(
                json.dumps(
                    {
                        "job_id": job_id,
                        "title": title,
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "style": job_style,
                        "options": options,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _job_status(job_id: str) -> str:
        live = active_runs.get(job_id)
        if live is not None and not live.done:
            return "running"
        try:
            snap = graph.get_state(cfg(job_id))
            if "approval" in (snap.next or ()):
                return "awaiting_approval"
            if snap.next:
                return "interrupted"  # stranded mid-run; the stream endpoint resumes it
            if _get(snap.values, "output_path"):
                return "done"
        except Exception:
            pass
        if (out_root / "runs" / job_id / "out.pptx").exists():
            return "done"
        if job_id in jobs or (states_dir / f"{job_id}.json").exists():
            return "created"
        return "expired"

    @app.post("/jobs")
    def create_job(req: CreateJob):
        job_id = req.job_id or uuid.uuid4().hex[:12]
        workspace = out_root / "assets" / job_id
        cache = out_root / "papers"  # shared content-addressed parse cache
        result = ingest(*req.inputs, workspace=workspace, cache_dir=cache) if req.inputs else None
        state = GenerationState(
            job_id=job_id,
            evidence=(result.assets if result else []),
            tables=(result.tables if result else []),
        )
        jobs[job_id] = state.model_dump()
        _save_state(job_id, state)
        _write_meta(job_id, Path(req.inputs[0]).name if req.inputs else job_id, "", {})
        return {"job_id": job_id, "status": "created"}

    @app.post("/jobs/upload")
    async def create_job_upload(
        files: list[UploadFile] = File(default=[]),
        style_name: str = Form(default=""),
        parser: str = Form(default=""),
        detail: str = Form(default="auto"),
        split_figures: bool = Form(default=False),
        vlm_critic: bool = Form(default=False),
        premium: bool = Form(default=True),
        native_formula: bool = Form(default=False),
    ):
        job_id = uuid.uuid4().hex[:12]
        job_dir = out_root / "uploads" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        for upload in files:
            dest = job_dir / (upload.filename or "upload.bin")
            dest.write_bytes(await upload.read())
            paths.append(str(dest))
        cache = out_root / "papers"  # shared content-addressed parse cache (dedup re-uploads)
        ingest_env = {
            "ASA_PDF_PARSER": parser or None,
            "ASA_SPLIT_FIGURES": "1" if split_figures else None,
        }
        with _env_overrides(ingest_env):
            result = ingest(*paths, workspace=job_dir, cache_dir=cache) if paths else None
        assets = result.assets if result else []
        options = {
            "vlm_critic": vlm_critic,
            "native_formula": native_formula,
            "split_figures": split_figures,
            "detail": (detail or "auto").lower(),
        }
        state = GenerationState(
            job_id=job_id,
            evidence=assets,
            tables=(result.tables if result else []),
            style=(style_name or None),
            options=options,
        )
        jobs[job_id] = state.model_dump()
        _save_state(job_id, state)
        title = Path(paths[0]).stem if paths else job_id
        _write_meta(job_id, title, style_name, options)
        return {
            "job_id": job_id,
            "status": "created",
            "title": title,
            "ingested": {
                "files": len(paths),
                "tables": len(result.tables) if result else 0,
                "figures": sum(1 for a in assets if a.kind == "figure"),
                "text_pages": sum(1 for a in assets if a.kind == "section_text"),
            },
            "warnings": (result.warnings if result else []),
        }

    # --- imported templates: extract theme tokens + inherit the master at compile time ----------
    templates_dir = out_root / "templates"

    def _rehydrate_templates() -> None:
        from pptx_compiler import profile_from_dict, register_style

        if not templates_dir.is_dir():
            return
        for tf in templates_dir.glob("*.json"):
            try:
                register_style(profile_from_dict(json.loads(tf.read_text(encoding="utf-8"))))
            except Exception:
                continue

    _rehydrate_templates()

    @app.post("/templates")
    async def upload_template(file: UploadFile = File(...), name: str = Form(default="")):
        from pptx_compiler import import_template, profile_to_dict

        tid = re.sub(r"[^a-z0-9_]+", "_", (name or Path(file.filename or "tpl").stem).lower())[:40] or "tpl"
        tdir = templates_dir / tid
        tdir.mkdir(parents=True, exist_ok=True)
        dest = tdir / "template.pptx"
        dest.write_bytes(await file.read())
        try:
            profile = import_template(dest, f"tpl_{tid}")
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"template import failed: {err}") from err
        (templates_dir / f"{tid}.json").write_text(
            json.dumps(profile_to_dict(profile), ensure_ascii=False), encoding="utf-8"
        )
        return {
            "style_name": profile.name,
            "fonts": [profile.ea_font, profile.latin_font],
            "accent": str(profile.accent_rgb),
        }

    @app.get("/templates")
    def list_templates():
        items = []
        if templates_dir.is_dir():
            for tf in templates_dir.glob("*.json"):
                try:
                    d = json.loads(tf.read_text(encoding="utf-8"))
                    items.append({"style_name": d.get("name"), "label": tf.stem, "accent": d.get("accent", "")})
                except Exception:
                    continue
        return {"templates": items}

    @app.get("/jobs")
    def list_jobs():
        items: list[dict] = []
        if meta_dir.is_dir():
            for mf in sorted(meta_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    meta = json.loads(mf.read_text(encoding="utf-8"))
                except Exception:
                    continue
                jid = meta.get("job_id") or mf.stem
                items.append(
                    {
                        "job_id": jid,
                        "title": meta.get("title") or jid,
                        "created_at": meta.get("created_at", ""),
                        "style": meta.get("style", ""),
                        "status": _job_status(jid),
                    }
                )
        return {"jobs": items}

    @app.delete("/jobs/{job_id}")
    def delete_job(job_id: str):
        jobs.pop(job_id, None)
        for sub in ("runs", "uploads", "assets"):
            shutil.rmtree(out_root / sub / job_id, ignore_errors=True)
        try:
            (meta_dir / f"{job_id}.json").unlink(missing_ok=True)
        except Exception:
            pass
        return {"job_id": job_id, "status": "deleted"}

    def _one_shot(event: str, data: dict):
        def gen():
            yield _sse(event, data)

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.get("/jobs/{job_id}/stream")
    def stream(job_id: str, reject: bool = False, feedback: str = ""):
        """Start, attach to, or resume a job's run. Execution is detached from this connection:
        a dropped client never aborts generation, and reconnecting replays the event log."""
        live = active_runs.get(job_id)
        if live is not None and not live.done and not reject:
            return StreamingResponse(_tail(live), media_type="text/event-stream")

        snap = None
        try:
            snap = graph.get_state(cfg(job_id))
        except Exception:
            pass
        nxt = (snap.next if snap else None) or ()

        if reject:  # resume a pending Hard-Stop with a rejection: replan streams live over SSE
            if "approval" not in nxt:
                raise HTTPException(status_code=409, detail="job is not awaiting approval")
            run = _start_run(job_id, Command(resume={"approved": False, "feedback": feedback}))
            return StreamingResponse(_tail(run), media_type="text/event-stream")
        if "approval" in nxt:  # already at the Hard-Stop (e.g. after reconnect/restart)
            return _one_shot("awaiting_approval", {"outline": _get(snap.values, "outline")})
        if nxt:  # stranded mid-run (e.g. killed between nodes) -> resume from the last checkpoint
            run = _start_run(job_id, None)
            return StreamingResponse(_tail(run), media_type="text/event-stream")
        if snap is not None and _get(snap.values, "output_path"):
            return _one_shot("done", {"output_path": _get(snap.values, "output_path")})

        initial = jobs.get(job_id) or _load_state(job_id)
        if initial is None:
            raise HTTPException(status_code=404, detail="job not found")
        run = _start_run(job_id, initial)
        return StreamingResponse(_tail(run), media_type="text/event-stream")

    @app.post("/jobs/{job_id}/preview")
    def build_preview(job_id: str):
        """Render the job's current deck (final out.pptx when present, else a draft compile of the
        in-flight slides) into per-slide PNGs for the visual approval / result views. Serialized per
        job (React dev double-mounts effects; concurrent renders would trample each other)."""
        from asa_agents.visual_critic import render_pptx_images

        with preview_locks[job_id]:
            try:
                run_dir = out_root / "runs" / job_id
                snap = None
                try:
                    snap = graph.get_state(cfg(job_id))
                except Exception:
                    pass
                values = (snap.values if snap else None) or {}
                out_path = _get(values, "output_path")
                src: Optional[Path] = None
                if out_path and Path(out_path).exists():
                    src = Path(out_path)
                elif (run_dir / "out.pptx").exists():
                    src = run_dir / "out.pptx"
                else:
                    slides = _get(values, "slides") or []
                    if not slides:
                        raise HTTPException(status_code=404, detail="nothing to preview yet")
                    from pptx_compiler import compile_deck

                    run_dir.mkdir(parents=True, exist_ok=True)
                    deck = Deck(deck_id=job_id, slides=slides)
                    evidence = _get(values, "evidence") or []
                    # Checkpoint round-trips deserialize models to dicts — never use attribute access here.
                    resolver = {
                        _get(a, "asset_id"): _get(a, "content_ref")
                        for a in evidence
                        if str(_get(a, "kind", "")) in ("figure", "EvidenceKind.FIGURE")
                    }
                    src = run_dir / "preview.pptx"
                    compile_deck(deck, src, asset_resolver=resolver, style=_get(values, "style") or style)
                png_dir = run_dir / "preview_png"
                # Reuse a fresh render: PNGs newer than the source mean nothing changed.
                pngs = _png_sorted(png_dir) if png_dir.is_dir() else []
                if pngs and pngs[0].stat().st_mtime >= src.stat().st_mtime:
                    return {"job_id": job_id, "count": len(pngs)}
                shutil.rmtree(png_dir, ignore_errors=True)
                images = render_pptx_images(src, png_dir)
                if not images:
                    raise HTTPException(
                        status_code=503, detail="no slide renderer available (LibreOffice/PowerPoint)"
                    )
                return {"job_id": job_id, "count": len(images)}
            except HTTPException:
                raise
            except Exception as err:  # surface as a JSON error WITH CORS headers (no opaque failures)
                raise HTTPException(status_code=500, detail=f"preview failed: {err}") from err

    @app.get("/jobs/{job_id}/preview/{idx}")
    def get_preview(job_id: str, idx: int):
        pngs = _png_sorted(out_root / "runs" / job_id / "preview_png")
        if idx < 1 or idx > len(pngs):
            raise HTTPException(status_code=404, detail="preview frame not found")
        return FileResponse(pngs[idx - 1], media_type="image/png")

    @app.post("/jobs/{job_id}/approve")
    def approve(job_id: str, req: Approve):
        snap = graph.get_state(cfg(job_id))
        if "approval" not in (snap.next or ()):
            raise HTTPException(status_code=409, detail="job is not awaiting approval")
        final = graph.invoke(
            Command(resume={"approved": req.approved, "edits": req.edits, "feedback": req.feedback}), cfg(job_id)
        )
        return {"job_id": job_id, "status": "done", "output_path": _get(final, "output_path")}

    def _download_name(job_id: str) -> str:
        """A human-readable filename: the paper title from job meta (sanitized), not the hex id."""
        title = ""
        try:
            meta = json.loads((meta_dir / f"{job_id}.json").read_text(encoding="utf-8"))
            title = (meta.get("title") or "").strip()
        except Exception:
            pass
        title = re.sub(r'[\\/:*?"<>|]+', " ", title).strip()[:80]
        return f"{title or job_id}.pptx"

    @app.get("/jobs/{job_id}/download")
    def download(job_id: str):
        out = None
        try:
            snap = graph.get_state(cfg(job_id))
            out = _get(snap.values, "output_path")
        except Exception:
            pass
        if not out or not Path(out).exists():  # disk fallback: survive server restarts
            disk = out_root / "runs" / job_id / "out.pptx"
            out = str(disk) if disk.exists() else None
        if not out:
            raise HTTPException(status_code=404, detail="deck not ready")
        return FileResponse(out, filename=_download_name(job_id), media_type=_PPTX_MIME)

    return app
