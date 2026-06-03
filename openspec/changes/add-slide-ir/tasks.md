## 1. Package setup

- [ ] 1.1 Create `packages/core/ir/` Python package (`pyproject.toml`, `__init__.py`)
- [ ] 1.2 Add `pydantic>=2` (MIT) as the only dependency; record it in `NOTICE`

## 2. Models

- [ ] 2.1 Implement block models (`FormulaBlock`, `TableBlock`, `BulletBlock`, `FigureBlock`) as a discriminated union on `type`
- [ ] 2.2 Implement `SlideIR` with a closed `layout_type` Enum and a `provenance` field
- [ ] 2.3 Implement `EvidenceAsset` and `GenerationState`

## 3. Validation

- [ ] 3.1 Enforce required fields (`table.columns`, `formula.latex`) with field validators
- [ ] 3.2 Reject unknown `layout_type` and unknown block `type`

## 4. JSON Schema export

- [ ] 4.1 Add `export_json_schema()` producing a valid JSON Schema for `SlideIR` + blocks
- [ ] 4.2 Write the schema to `packages/core/ir/schema/slide_ir.schema.json`

## 5. Tests

- [ ] 5.1 Valid IR fixtures parse successfully (one per `layout_type`)
- [ ] 5.2 Invalid IR fixtures fail (missing `columns`/`latex`, unknown types)
- [ ] 5.3 Round-trip: model → JSON → model is identity
- [ ] 5.4 JSON Schema export is a valid schema document
