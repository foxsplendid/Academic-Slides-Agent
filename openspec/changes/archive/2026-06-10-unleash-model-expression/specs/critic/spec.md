## MODIFIED Requirements

### Requirement: Layout monotony detection
Monotony findings SHALL be advisory (worded without the repair-routing token) so they inform the
human at the Hard-Stop without consuming the bounded repair budget.

#### Scenario: Monotony does not burn retries
- **WHEN** five consecutive slides share a layout and nothing else is wrong
- **THEN** the deck reaches approval with the advisory finding attached
