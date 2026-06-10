## ADDED Requirements

### Requirement: Fail-open repair
The repair pass SHALL enumerate the legal block vocabulary in its prompt, normalize high-frequency
near-misses (a table's title becomes its caption) before validation, and keep the original slide when
a repair exhausts its retries so the run always reaches the Hard-Stop.

#### Scenario: Exhausted repair keeps the slide
- **WHEN** a flagged slide's repair fails validation on every attempt
- **THEN** the original slide is kept and generation proceeds to approval
