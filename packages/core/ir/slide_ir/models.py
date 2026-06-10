"""Slide-IR — the validated, template-agnostic intermediate representation.

The LLM emits ONLY Slide-IR; a deterministic, AI-free compiler consumes it.
See docs/SPEC.md sections 3.1 and 4. This module is pure data (Pydantic v2):
no AI, no rendering, no orchestration imports.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class LayoutType(str, Enum):
    """Closed vocabulary of slide layouts.

    Extend ONLY via an OpenSpec change that also updates docs/SPEC.md — never ad-hoc.
    """

    TITLE = "title"
    SECTION = "section"
    BULLET_EVIDENCE = "bullet_evidence"
    TWO_COLUMN_TABLE = "two_column_table"
    FORMULA_BANNER = "formula_banner"
    FIGURE_CAPTION = "figure_caption"  # figure right, text left (figure-led)
    FIGURE_LEFT = "figure_left"  # figure left, text right
    TWO_CONTENT = "two_content"  # any two blocks side by side
    FIGURE_GRID = "figure_grid"  # 2-4 figures in a grid
    BIG_FIGURE = "big_figure"  # one dominant figure, minimal text


# --------------------------------------------------------------------------- #
# Content blocks — a discriminated union on `type`.                            #
# `extra="forbid"` makes every block a strict contract (unknown fields fail).  #
# --------------------------------------------------------------------------- #


class _BlockBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FormulaBlock(_BlockBase):
    type: Literal["formula"] = "formula"
    latex: str = Field(min_length=1)  # required & non-empty
    render_tier: Literal["auto", "omml", "svg", "png"] = "auto"  # v1 resolves to svg
    rendered_ref: Optional[str] = None  # compiler fills the rendered asset id/path


class TableBlock(_BlockBase):
    type: Literal["table"] = "table"
    columns: list[str] = Field(min_length=1)  # required & non-empty
    rows: list[list[str]] = Field(default_factory=list)
    caption: Optional[str] = None
    highlight: Optional[dict] = None
    needs_human_check: bool = True  # PDF-extracted tables default to human review


class BulletItem(BaseModel):
    """A bullet with optional sub-bullets (one nesting level)."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    children: list[str] = Field(default_factory=list)


class BulletBlock(_BlockBase):
    type: Literal["bullets"] = "bullets"
    items: list[Union[str, BulletItem]] = Field(min_length=1)


class CalloutBlock(_BlockBase):
    """An emphasized takeaway/conclusion band (rendered as a tinted card with an accent edge)."""

    type: Literal["callout"] = "callout"
    text: str = Field(min_length=1)
    label: Optional[str] = None  # short tag, e.g. "结论" / "Take-away"


class StatItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1)  # the big number, e.g. "94%" / "r=0.938"
    label: str = ""  # what it measures


class StatBlock(_BlockBase):
    """1-4 key numbers as big-number cards in a row."""

    type: Literal["stat"] = "stat"
    items: list[StatItem] = Field(min_length=1, max_length=4)


class FigureBlock(_BlockBase):
    type: Literal["figure"] = "figure"
    asset_id: str = Field(min_length=1)  # references an Evidence Pool figure
    caption: Optional[str] = None


class ChartSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = ""
    values: list[float] = Field(min_length=1)  # y-values (category charts) or y (scatter)
    x: Optional[list[float]] = None  # scatter only: x-values paired with `values`


class ChartBlock(_BlockBase):
    type: Literal["chart"] = "chart"
    chart_type: Literal["bar", "line", "scatter", "pie"] = "bar"
    categories: list[str] = Field(default_factory=list)  # x-axis labels for bar/line/pie
    series: list[ChartSeries] = Field(min_length=1)
    title: Optional[str] = None


class DiagramNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)


class DiagramEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)  # a node id
    target: str = Field(min_length=1)  # a node id
    label: Optional[str] = None


class DiagramBlock(_BlockBase):
    """A SEMANTIC logic diagram — nodes + edges + type, NO coordinates. The deterministic compiler
    computes the layout, so the LLM never emits geometry (no coordinate hallucination)."""

    type: Literal["diagram"] = "diagram"
    diagram_type: Literal["flow", "tree", "cycle", "comparison", "pyramid", "timeline"] = "flow"
    nodes: list[DiagramNode] = Field(min_length=1)
    edges: list[DiagramEdge] = Field(default_factory=list)
    title: Optional[str] = None


Block = Annotated[
    Union[FormulaBlock, TableBlock, BulletBlock, FigureBlock, ChartBlock, DiagramBlock, CalloutBlock, StatBlock],
    Field(discriminator="type"),
]


# --------------------------------------------------------------------------- #
# Slide & Deck                                                                 #
# --------------------------------------------------------------------------- #


class SlideIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slide_id: str = Field(min_length=1)
    layout_type: LayoutType
    title: str = ""
    blocks: list[Block] = Field(default_factory=list)
    speaker_notes: str = ""
    provenance: dict = Field(default_factory=dict)  # links content back to Evidence Pool


class Deck(BaseModel):
    """An ordered list of Slide-IR — the unit the compiler renders to .pptx."""

    model_config = ConfigDict(extra="forbid")

    deck_id: str = Field(min_length=1)
    slides: list[SlideIR] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Evidence Pool & workflow state                                              #
# --------------------------------------------------------------------------- #


class EvidenceKind(str, Enum):
    SECTION_TEXT = "section_text"
    TABLE = "table"
    FIGURE = "figure"
    DATASET = "dataset"


class EvidenceAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(min_length=1)
    kind: EvidenceKind
    content_ref: str  # text / dataframe handle / file path
    source: str = Field(min_length=1)  # "paper.pdf" | "supp.xlsx#Sheet1" | ...
    locator: dict = Field(default_factory=dict)  # {"page":7} | {"sheet":"S1"} | {"section":"4.2"}


class Phase(str, Enum):
    INGESTING = "ingesting"
    ABSTRACTING = "abstracting"
    OUTLINING = "outlining"
    AWAIT_OUTLINE_APPROVAL = "await_outline_approval"  # Hard-Stop landing point
    MAPPING = "mapping"
    COMPILING = "compiling"
    CRITIQUING = "critiquing"
    EXPORTING = "exporting"
    DONE = "done"
    ERROR = "error"


class GenerationState(BaseModel):
    """LangGraph state: checkpointed (resume) + streamed + Hard-Stop carrier.

    Intentionally permissive (no extra="forbid") so the orchestration layer can extend it.
    """

    job_id: str = Field(min_length=1)
    phase: Phase = Phase.INGESTING
    source_kind: Literal["pdf", "tex"] = "pdf"
    evidence: list[EvidenceAsset] = Field(default_factory=list)
    tables: list[TableBlock] = Field(default_factory=list)
    outline: Optional[list[dict]] = None
    user_approved_outline: bool = False
    user_outline_edits: Optional[list[dict]] = None
    slides: list[SlideIR] = Field(default_factory=list)
    output_path: Optional[str] = None
    template_id: Optional[str] = None
    critic_findings: list[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2
    error: Optional[str] = None


# --------------------------------------------------------------------------- #
# The LLM output boundary                                                      #
# --------------------------------------------------------------------------- #


class IRBoundaryError(ValueError):
    """Raised when content offered as Slide-IR fails the contract."""


def from_llm_output(raw: Union[str, dict]) -> Deck:
    """The single boundary the LLM's output must pass.

    Agents may only emit Slide-IR; anything that is not a valid Deck is rejected here and
    never reaches the compiler. Accepts a JSON string or a parsed dict.
    """
    try:
        if isinstance(raw, str):
            return Deck.model_validate_json(raw)
        return Deck.model_validate(raw)
    except ValidationError as exc:
        raise IRBoundaryError(f"LLM output is not valid Slide-IR: {exc}") from exc
