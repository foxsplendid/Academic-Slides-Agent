"""Slide-IR — the data contract for Academic-Slides-Agent.

The LLM emits ONLY Slide-IR; a deterministic compiler consumes it. See docs/SPEC.md.
"""

from .models import (
    Block,
    BulletBlock,
    BulletItem,
    CalloutBlock,
    ChartBlock,
    ChartSeries,
    Deck,
    DiagramBlock,
    DiagramEdge,
    DiagramNode,
    EvidenceAsset,
    EvidenceKind,
    FigureBlock,
    FormulaBlock,
    GenerationState,
    IRBoundaryError,
    LayoutType,
    Phase,
    SlideIR,
    StatBlock,
    StatItem,
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
    "BulletItem",
    "CalloutBlock",
    "StatBlock",
    "StatItem",
    "FigureBlock",
    "ChartBlock",
    "ChartSeries",
    "DiagramBlock",
    "DiagramNode",
    "DiagramEdge",
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
