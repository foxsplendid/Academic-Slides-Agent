## ADDED Requirements

### Requirement: Structural narrative layouts
The IR SHALL provide `toc` (agenda) and `ending` (closing) layout values; `ending` SHALL be a
divider (no content blocks) and `toc` SHALL carry its agenda as a bullets block.

#### Scenario: toc validates with agenda bullets
- **WHEN** a slide declares layout `toc` with a bullets block of section names
- **THEN** it passes IR validation
