"""``lectern`` — a headless CLI for Academic-Slides-Agent.

Three commands, all thin drivers over the SAME graph/checkpointer/compiler the FastAPI app uses:

  lectern build <handoff-dir|pdf> [--out deck.pptx] [--style ...] [--provider ...]
      Run the FULL pipeline headless, AUTO-APPROVING the outline gate, and write the .pptx.

  lectern outline <handoff-dir|pdf> --out outline.json [--style ...] [--provider ...]
      Run up to the outline interrupt, dump the (editable) outline to JSON, and exit. The graph
      state is checkpointed durably, so a later `build --from-outline` resumes the SAME run.

  lectern build --from-outline outline.json --out deck.pptx
      Resume the paused run from an approved/edited outline.json -> compile -> .pptx.

The outline gate is the human review point made OPTIONAL: `build` auto-approves it; the
`outline` + `build --from-outline` pair turns it into a file contract an agent or human can edit.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Optional

from langgraph.types import Command

from .driver import build_cli_graph, cfg, field, ingest_to_state, load_env


def _new_job_id() -> str:
    return uuid.uuid4().hex[:12]


def _set_provider(provider: Optional[str]) -> None:
    if provider:
        import os

        os.environ["ASA_LLM_PROVIDER"] = provider


def _emit_outline(outline, stream=sys.stderr) -> None:
    for i, slide in enumerate(outline or [], 1):
        title = slide.get("title", "") if isinstance(slide, dict) else getattr(slide, "title", "")
        layout = slide.get("layout_type", "") if isinstance(slide, dict) else getattr(slide, "layout_type", "")
        print(f"  {i:>2}. [{layout}] {title}", file=stream)


def _copy_out(produced: str | Path, dest: Optional[str | Path]) -> Path:
    """Copy the graph's run output (`<out>/runs/<job>/out.pptx`) to the user's --out path."""
    produced = Path(produced)
    if dest is None:
        return produced
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(produced, dest)
    return dest


# --------------------------------------------------------------------------- #
# Commands                                                                     #
# --------------------------------------------------------------------------- #


def _resume_approved(graph, thread_id: str, edits=None):
    """Resume the paused run past the outline gate with an approval — the SAME call the API's
    approve handler makes (app.py:522). Returns the final state."""
    return graph.invoke(Command(resume={"approved": True, "edits": edits, "feedback": None}), cfg(thread_id))


def cmd_build(args) -> int:
    _set_provider(args.provider)
    out_dir = Path(args.work_dir)

    # ---- resume path: build --from-outline outline.json -----------------------------------------
    if args.from_outline:
        contract = json.loads(Path(args.from_outline).read_text(encoding="utf-8"))
        job_id = contract["job_id"]
        out_dir = Path(contract.get("out_dir", out_dir))
        edits = contract.get("edits")  # optional outline edits the reviewer wrote into the contract
        graph = build_cli_graph(out_dir=out_dir, style=args.style)
        snap = graph.get_state(cfg(job_id))
        if "approval" not in (snap.next or ()):
            print(
                f"error: thread '{job_id}' is not awaiting approval (checkpoint missing or already "
                f"compiled). Re-run `lectern outline` to recreate the paused run.",
                file=sys.stderr,
            )
            return 2
        final = _resume_approved(graph, job_id, edits=edits)
        produced = field(final, "output_path")
        if not produced:
            print("error: resume did not produce an output_path", file=sys.stderr)
            return 1
        written = _copy_out(produced, args.out)
        print(str(written))
        return 0

    # ---- full headless build (auto-approve) ------------------------------------------------------
    job_id = _new_job_id()
    state, result = ingest_to_state(
        args.source, job_id=job_id, out_dir=out_dir, style=args.style
    )
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not state.evidence:
        print(f"error: nothing ingested from {args.source!r}", file=sys.stderr)
        return 2

    graph = build_cli_graph(out_dir=out_dir, style=args.style)
    graph.invoke(state.model_dump(), cfg(job_id))  # runs plan -> critic -> pauses at the approval gate
    snap = graph.get_state(cfg(job_id))
    if "approval" in (snap.next or ()):
        print("outline (auto-approved):", file=sys.stderr)
        _emit_outline(field(snap.values, "outline"))
        final = _resume_approved(graph, job_id)
    else:
        final = snap.values  # already terminal (no gate) — defensive, the graph always gates

    produced = field(final, "output_path")
    if not produced:
        print("error: pipeline did not produce an output_path", file=sys.stderr)
        return 1
    written = _copy_out(produced, args.out)
    print(str(written))
    return 0


def cmd_outline(args) -> int:
    _set_provider(args.provider)
    out_dir = Path(args.work_dir)
    job_id = _new_job_id()
    state, result = ingest_to_state(
        args.source, job_id=job_id, out_dir=out_dir, style=args.style
    )
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not state.evidence:
        print(f"error: nothing ingested from {args.source!r}", file=sys.stderr)
        return 2

    graph = build_cli_graph(out_dir=out_dir, style=args.style)
    graph.invoke(state.model_dump(), cfg(job_id))  # pauses at the approval gate (durable checkpoint)
    snap = graph.get_state(cfg(job_id))
    if "approval" not in (snap.next or ()):
        print("error: run did not reach the outline gate", file=sys.stderr)
        return 1

    outline = field(snap.values, "outline") or []
    contract = {
        "schema": "lectern-outline/1",
        "job_id": job_id,
        "out_dir": str(out_dir),
        "source": str(args.source),
        "style": args.style,
        "outline": outline,  # editable: a reviewer may tweak titles, or drop slides
        "edits": None,  # optional: structured edits passed back to the graph on resume
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    print("outline written for review:", file=sys.stderr)
    _emit_outline(outline)
    print(str(out_path))
    return 0


# --------------------------------------------------------------------------- #
# Parser                                                                       #
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lectern", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--style", default=None, help="StyleProfile name (e.g. academic, modern_teal)")
    common.add_argument("--provider", default=None, help="LLM provider override (sets ASA_LLM_PROVIDER)")
    common.add_argument(
        "--work-dir",
        default="exports",
        help="Working/output root for runs, cache, and the durable checkpoint (default: exports)",
    )

    p_build = sub.add_parser(
        "build", parents=[common], help="Full headless pipeline -> .pptx (auto-approves the outline gate)"
    )
    p_build.add_argument("source", nargs="?", help="handoff dir or PDF (omit when using --from-outline)")
    p_build.add_argument("--out", default=None, help="Destination .pptx path")
    p_build.add_argument(
        "--from-outline", default=None, help="Resume from an approved outline.json (file contract)"
    )
    p_build.set_defaults(func=cmd_build)

    p_outline = sub.add_parser(
        "outline", parents=[common], help="Run to the outline gate and dump outline.json, then exit"
    )
    p_outline.add_argument("source", help="handoff dir or PDF")
    p_outline.add_argument("--out", required=True, help="Destination outline.json path")
    p_outline.set_defaults(func=cmd_outline)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    load_env()  # pick up provider keys from a local .env
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "build" and not args.source and not args.from_outline:
        parser.error("build requires a source, or --from-outline")
    rc = args.func(args)
    return int(rc or 0)


if __name__ == "__main__":
    raise SystemExit(main())
