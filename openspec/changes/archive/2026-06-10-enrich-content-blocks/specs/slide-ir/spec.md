## ADDED Requirements

### Requirement: Rich content blocks
The IR SHALL support one level of bullet nesting (`BulletItem` with children), a `callout` block
(labelled takeaway text), and a `stat` block (1-4 value/label items), all validated strictly.

#### Scenario: Nested bullets validate
- **WHEN** a bullets block mixes plain strings and a BulletItem with children
- **THEN** it passes IR validation
