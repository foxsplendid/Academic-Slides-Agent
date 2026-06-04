## ADDED Requirements

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
