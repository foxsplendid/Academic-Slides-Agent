## MODIFIED Requirements

### Requirement: Rich content blocks
Stat blocks SHALL accept any number of items at the schema level (at least one); row-fit limits are
enforced by the critic as repairable findings rather than hard schema rejections.

#### Scenario: Oversized stat row routes to repair
- **WHEN** a stat block carries five items
- **THEN** the deck validates and the critic flags the slide for repair
