"""Unit tests for Slide-IR.

Each test maps to a scenario in
openspec/changes/add-slide-ir/specs/slide-ir/spec.md.
"""

from __future__ import annotations

import json

import jsonschema
import pytest
from pydantic import ValidationError

from slide_ir import (
    Deck,
    EvidenceAsset,
    FigureBlock,
    FormulaBlock,
    BulletBlock,
    GenerationState,
    IRBoundaryError,
    LayoutType,
    SlideIR,
    TableBlock,
    export_json_schema,
    from_llm_output,
)


# --- Requirement: Closed layout vocabulary ---


@pytest.mark.parametrize("lt", [e.value for e in LayoutType])
def test_known_layout_type_accepted(lt):
    assert SlideIR(slide_id="s1", layout_type=lt, title="t").layout_type.value == lt


def test_unknown_layout_type_rejected():
    with pytest.raises(ValidationError):
        SlideIR(slide_id="s1", layout_type="totally_unknown", title="t")


# --- Requirement: Typed content blocks via discriminated union ---


def test_block_parsed_to_concrete_type():
    s = SlideIR.model_validate(
        {
            "slide_id": "s1",
            "layout_type": "two_column_table",
            "title": "t",
            "blocks": [{"type": "table", "columns": ["a", "b"], "rows": [["1", "2"]]}],
        }
    )
    assert isinstance(s.blocks[0], TableBlock)
    assert s.blocks[0].columns == ["a", "b"]


def test_unknown_block_type_rejected():
    with pytest.raises(ValidationError):
        SlideIR.model_validate(
            {"slide_id": "s1", "layout_type": "section", "title": "t", "blocks": [{"type": "nope"}]}
        )


# --- Requirement: Validation rejects malformed IR ---


def test_table_without_columns_rejected():
    with pytest.raises(ValidationError):
        TableBlock(rows=[["1"]])


def test_table_with_empty_columns_rejected():
    with pytest.raises(ValidationError):
        TableBlock(columns=[], rows=[])


def test_formula_without_latex_rejected():
    with pytest.raises(ValidationError):
        FormulaBlock()


def test_formula_with_empty_latex_rejected():
    with pytest.raises(ValidationError):
        FormulaBlock(latex="")


# --- Requirement: Provenance for anti-hallucination ---


def test_slide_retains_provenance():
    s = SlideIR(slide_id="s1", layout_type="section", title="t", provenance={"source_section": "4.2"})
    assert s.provenance == {"source_section": "4.2"}


def test_evidence_asset_records_source_and_locator():
    a = EvidenceAsset(
        asset_id="e1", kind="table", content_ref="df://1", source="supp.xlsx#S1", locator={"sheet": "S1"}
    )
    assert a.source == "supp.xlsx#S1"
    assert a.locator == {"sheet": "S1"}


# --- Requirement: JSON Schema export ---


def test_json_schema_is_valid_document():
    schema = export_json_schema()
    jsonschema.Draft202012Validator.check_schema(schema)  # raises if not a valid schema
    assert schema["type"] == "object"


# --- Requirement: LLM output boundary ---


def test_valid_llm_output_accepted():
    raw = json.dumps(
        {
            "deck_id": "d1",
            "slides": [
                {
                    "slide_id": "s1",
                    "layout_type": "formula_banner",
                    "title": "t",
                    "blocks": [{"type": "formula", "latex": "E=mc^2"}],
                }
            ],
        }
    )
    deck = from_llm_output(raw)
    assert isinstance(deck, Deck)
    assert isinstance(deck.slides[0].blocks[0], FormulaBlock)


def test_non_ir_output_rejected_at_boundary():
    with pytest.raises(IRBoundaryError):
        from_llm_output('{"foo": "not a deck", "slides": [{"bad": true}]}')


def test_garbage_string_rejected_at_boundary():
    with pytest.raises(IRBoundaryError):
        from_llm_output("this is not json at all")


# --- Round-trip identity ---


def test_round_trip_identity():
    deck = Deck(
        deck_id="d1",
        slides=[
            SlideIR(
                slide_id="s1",
                layout_type=LayoutType.BULLET_EVIDENCE,
                title="T",
                blocks=[BulletBlock(items=["one", "two"]), FigureBlock(asset_id="fig1", caption="c")],
                provenance={"source_page": 7},
            )
        ],
    )
    restored = Deck.model_validate_json(deck.model_dump_json())
    assert restored == deck


def test_generation_state_defaults():
    st = GenerationState(job_id="j1")
    assert st.phase.value == "ingesting"
    assert st.max_retries == 2
