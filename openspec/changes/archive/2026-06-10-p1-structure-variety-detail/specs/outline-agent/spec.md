## ADDED Requirements

### Requirement: Deck-level design planning and density contracts
The skeleton planner SHALL treat layout assignment as a deck-level design decision (structure pages,
alternating figure sides, no long same-layout runs) and SHALL receive a quantified density contract
(page budget, bullets and notes quotas) selected by the job's detail level; the expansion prompt
SHALL carry the same per-slide quotas and a chart-type selection taxonomy.

#### Scenario: Detail level changes the quotas
- **WHEN** a deck is built with detail "high"
- **THEN** the skeleton prompt carries the 12-16 page budget and expansions carry the 5-7 bullet quota
