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

### Requirement: Chart block
Slide-IR SHALL include a `ChartBlock` (`type: "chart"`) carrying a `chart_type`
(`bar`|`line`|`scatter`|`pie`), `categories`, and one or more `series` of `{name, values, x?}`, so the
LLM can request a native data chart through the strict IR boundary.

#### Scenario: A valid chart block is accepted
- **WHEN** a deck contains a `chart` block with a known `chart_type` and at least one series
- **THEN** it passes the IR boundary

#### Scenario: An invalid chart block is rejected
- **WHEN** a `chart` block has an unknown `chart_type` or no series
- **THEN** the IR boundary rejects it

### Requirement: Diagram block
Slide-IR SHALL include a `DiagramBlock` (`type: "diagram"`) carrying a `diagram_type`
(flow|tree|cycle|comparison|pyramid|timeline), one or more `nodes` (`{id, label}`), and optional
`edges` (`{source, target, label?}`) — a **semantic** structure with no coordinates — so the LLM can
request a logic diagram through the strict IR boundary.

#### Scenario: A valid diagram is accepted
- **WHEN** a deck contains a `diagram` block with a known `diagram_type` and at least one node
- **THEN** it passes the IR boundary

#### Scenario: An invalid diagram is rejected
- **WHEN** a `diagram` block has an unknown `diagram_type` or no nodes
- **THEN** the IR boundary rejects it

### Requirement: Composition layout vocabulary
The IR SHALL provide layout values for the recurring academic compositions: `figure_left` (figure
left, text right), `two_content` (two blocks side by side), `figure_grid` (2-4 figures in a grid),
and `big_figure` (one dominant figure), in addition to the existing layouts.

#### Scenario: New layouts validate
- **WHEN** a slide declares `layout_type: "figure_grid"`
- **THEN** it passes IR validation

### Requirement: Rich content blocks
Stat blocks SHALL accept any number of items at the schema level (at least one); row-fit limits are
enforced by the critic as repairable findings rather than hard schema rejections.

#### Scenario: Oversized stat row routes to repair
- **WHEN** a stat block carries five items
- **THEN** the deck validates and the critic flags the slide for repair

### Requirement: Structural narrative layouts
The IR SHALL provide `toc` (agenda) and `ending` (closing) layout values; `ending` SHALL be a
divider (no content blocks) and `toc` SHALL carry its agenda as a bullets block.

#### Scenario: toc validates with agenda bullets
- **WHEN** a slide declares layout `toc` with a bullets block of section names
- **THEN** it passes IR validation

### Requirement: Concept icons on cards
Callout blocks and stat items SHALL accept an optional icon name from a closed whitelist.

#### Scenario: Icon field validates
- **WHEN** a callout declares icon "bulb"
- **THEN** it passes IR validation

### Requirement: Slide subtitle
A slide SHALL accept an optional subtitle (cover meta line, content kicker, or divider lead-in).

#### Scenario: Subtitle validates
- **WHEN** a content slide carries a one-line subtitle
- **THEN** it passes IR validation

### Requirement: Canvas block (premium)
The IR SHALL offer a canvas block carrying a full-page constrained SVG composition for the premium
tier; the canvas layout type SHALL carry exactly one canvas block.

#### Scenario: Canvas block validates
- **WHEN** a canvas slide carries one canvas block with a well-formed SVG
- **THEN** it passes IR validation

