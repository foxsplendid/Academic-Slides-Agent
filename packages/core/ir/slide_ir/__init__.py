"""Slide-IR — the data contract for Academic-Slides-Agent.

The LLM emits ONLY Slide-IR; a deterministic compiler consumes it. See docs/SPEC.md.
"""

from .models import (
    Block,
    BulletBlock,
    ChartBlock,
    ChartSeries,
    Deck,
    EvidenceAsset,
    EvidenceKind,
    FigureBlock,
    FormulaBlock,
    GenerationState,
    IRBoundaryError,
    LayoutType,
    Phase,
    SlideIR,
    TableBlock,
    from_llm_output,
)
from .schema import export_json_schema, write_schema

__all__ = [
    "LayoutType",
    "Phase",
    "EvidenceKind",
    "FormulaBlock",
    "TableBlock",
    "BulletBlock",
    "FigureBlock",
    "ChartBlock",
    "ChartSeries",
    "Block",
    "SlideIR",
    "Deck",
    "EvidenceAsset",
    "GenerationState",
    "from_llm_output",
    "IRBoundaryError",
    "export_json_schema",
    "write_schema",
]
