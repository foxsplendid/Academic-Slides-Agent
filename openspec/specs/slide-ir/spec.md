# slide-ir Specification

## Purpose
TBD - created by archiving change add-slide-ir. Update Purpose after archive.
## Requirements
### Requirement: Closed layout vocabulary
The Slide-IR SHALL define `layout_type` as a closed, enumerated vocabulary. The system SHALL
reject any slide whose `layout_type` is not in the vocabulary.

#### Scenario: Unknown layout type is rejected
- **WHEN** an IR slide declares a `layout_type` not in the defined vocabulary
- **THEN** validation fails with an error identifying the offending slide

#### Scenario: Known layout type is accepted
- **WHEN** an IR slide declares a `layout_type` from the vocabulary (e.g. `two_column_table`)
- **THEN** validation succeeds

### Requirement: Typed content blocks via discriminated union
Each content block SHALL be one of a fixed set of typed blocks (`formula`, `table`, `bullets`,
`figure`), discriminated by a `type` field. The system SHALL parse each block into its concrete
type based on `type`.

#### Scenario: Block parsed to concrete type
- **WHEN** a block with `"type": "table"` is parsed
- **THEN** it is materialized as a TableBlock exposing `columns` and `rows`

#### Scenario: Unknown block type is rejected
- **WHEN** a block declares a `type` outside the fixed set
- **THEN** validation fails

### Requirement: Validation rejects malformed IR
The system SHALL reject structurally invalid IR before any rendering, including a `table` block
missing `columns` and a `formula` block missing `latex`.

#### Scenario: Table without columns is rejected
- **WHEN** a TableBlock is constructed without `columns`
- **THEN** validation fails with a field-level error

#### Scenario: Formula without latex is rejected
- **WHEN** a FormulaBlock is constructed without `latex`
- **THEN** validation fails with a field-level error

### Requirement: Provenance for anti-hallucination
Each slide SHALL be able to carry `provenance` linking its content back to an Evidence Pool
source. Each `EvidenceAsset` SHALL record its `source` and `locator`.

#### Scenario: Slide retains provenance
- **WHEN** a slide is created with `provenance` `{"source_section": "4.2"}`
- **THEN** the parsed slide exposes that provenance unchanged

### Requirement: JSON Schema export
The system SHALL export the Slide-IR models to JSON Schema so external consumers (e.g. the
frontend) can generate matching types.

#### Scenario: Schema is exported
- **WHEN** schema export is invoked
- **THEN** a valid JSON Schema document describing `SlideIR` and its blocks is produced

### Requirement: LLM output boundary
Slide-IR SHALL be the only structure agents are permitted to emit. Agents SHALL NOT emit SVG,
executable code, or `.pptx`; their output MUST validate as Slide-IR.

#### Scenario: Non-IR agent output is rejected at the boundary
- **WHEN** an agent returns content that is not valid Slide-IR
- **THEN** the boundary rejects it and does not pass it to the compiler

