## ADDED Requirements

### Requirement: Tunable, measurable, depth-safe expansion latency
The detailed builder SHALL read expansion concurrency from `ASA_EXPAND_WORKERS` (default 6), SHALL cap
per-slide evidence adaptively (full context for figure/table slides, tighter for plain bullet slides),
and SHALL constrain output length (concise speaker notes and bullets) without reducing the substantive
bullet count. When `ASA_DEBUG_TIMING` is set it SHALL emit a timing event reporting wall time versus the
sum of per-call times.

#### Scenario: Concurrency is tunable via env
- **WHEN** `ASA_EXPAND_WORKERS=2` and a multi-slide deck is expanded
- **THEN** at most two slide expansions are in flight at once

#### Scenario: Evidence is capped adaptively
- **WHEN** a plain bullet slide and a figure slide reference an over-long page
- **THEN** the plain slide's prompt carries less evidence than the figure slide's
