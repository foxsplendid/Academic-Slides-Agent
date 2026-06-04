# orchestration Specification

## Purpose
TBD - created by archiving change add-langgraph-orchestration. Update Purpose after archive.
## Requirements
### Requirement: Orchestrate outline to native deck
The graph SHALL run outline planning, human approval, and compilation in order, producing a native
`.pptx` whose path is recorded in the state.

#### Scenario: Full run produces a deck
- **WHEN** the graph runs to completion (outline approved)
- **THEN** a `.pptx` file exists at the state's `output_path`

### Requirement: Human Hard-Stop via interrupt
The graph SHALL pause at an interrupt for outline approval and SHALL NOT compile until resumed.

#### Scenario: First run pauses before compiling
- **WHEN** the graph is invoked and reaches the approval node
- **THEN** execution pauses (an interrupt is surfaced) and no `.pptx` has been written yet

### Requirement: Resume after approval
The graph SHALL resume from its checkpoint when given the approval payload and continue to compile.

#### Scenario: Resuming with approval completes the run
- **WHEN** the paused graph is resumed with an approval command
- **THEN** the run continues, records the approval, and writes the `.pptx`

### Requirement: Streaming of node progress
The graph SHALL stream per-node updates as it runs.

#### Scenario: Streaming emits updates
- **WHEN** the graph is streamed
- **THEN** at least one per-node update is emitted before the interrupt

### Requirement: IR boundary is enforced before rendering
If the LLM output is not valid Slide-IR, the graph SHALL fail in the planning node and SHALL NOT
produce a deck.

#### Scenario: Non-IR output aborts before compile
- **WHEN** the LLM returns non-IR text
- **THEN** planning raises and no `.pptx` is written

### Requirement: Injectable planner
The graph SHALL accept an injectable planner callable (default: the single-shot `build_outline`) so a
detailed multi-stage planner can drive production runs without changing the graph's structure.

#### Scenario: Default planner is unchanged
- **WHEN** a graph is built without specifying a planner
- **THEN** it plans with the single-shot builder and reaches the approval Hard-Stop as before

#### Scenario: A custom planner is used
- **WHEN** a graph is built with a custom planner callable
- **THEN** the plan node uses that callable to produce the deck

