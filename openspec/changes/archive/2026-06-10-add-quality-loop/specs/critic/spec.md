## ADDED Requirements

### Requirement: Render-grounded quality checks
The quality loop SHALL include a deterministic post-compile geometry lint (text at the auto-shrink
floor, figure-led slides with tiny figures, overlapping content shapes) whose findings name the slide
for repair, and MAY include an opt-in VLM visual critique restricted to a closed defect taxonomy that
emits IR-level suggestions. Both stages SHALL fail open (a check failure never blocks generation).

#### Scenario: Crammed text is flagged for repair
- **WHEN** a compiled slide's body text sits at the auto-shrink floor
- **THEN** a finding names that slide and suggests shortening or splitting

#### Scenario: VLM critique is taxonomy-bound
- **WHEN** the vision model reports a defect outside the closed taxonomy
- **THEN** it is discarded
