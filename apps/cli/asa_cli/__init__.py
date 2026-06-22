"""asa_cli — a headless CLI driver for Lectern.

It reuses the SAME compiled LangGraph + checkpointer + deterministic compiler the FastAPI service
uses; the CLI only composes those parts (ingest -> invoke -> resume) and never reimplements the
pipeline or the IR/compile logic.
"""

from .driver import build_cli_graph, ingest_to_state

__all__ = ["build_cli_graph", "ingest_to_state"]
