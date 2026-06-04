## ADDED Requirements

### Requirement: Parallel slide expansion with serial fallback
The two-stage builder SHALL expand slides concurrently by default and SHALL fall back to serial
expansion if the parallel path raises, always returning slides in skeleton order.

#### Scenario: Parallel expansion preserves order
- **WHEN** the detailed builder expands a multi-slide skeleton in parallel
- **THEN** the returned deck's slides are in the skeleton's order

#### Scenario: Failure falls back to serial
- **WHEN** a parallel worker raises during expansion
- **THEN** the builder retries serially and still returns a valid deck

### Requirement: Progress reporting
The two-stage builder SHALL accept a progress callback and invoke it for the skeleton stage and for
each expanded slide with a done/total count.

#### Scenario: Progress callback receives slide counts
- **WHEN** the builder runs with a progress callback
- **THEN** the callback is invoked with slide `done` and `total` values
