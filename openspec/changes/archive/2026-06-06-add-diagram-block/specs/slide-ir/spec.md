## ADDED Requirements

### Requirement: Diagram block
Slide-IR SHALL include a `DiagramBlock` (`type: "diagram"`) carrying a `diagram_type`
(flow|tree|cycle|comparison|pyramid|timeline), one or more `nodes` (`{id, label}`), and optional
`edges` (`{source, target, label?}`) — a **semantic** structure with no coordinates — so the LLM can
request a logic diagram through the strict IR boundary.

#### Scenario: A valid diagram is accepted
- **WHEN** a deck contains a `diagram` block with a known `diagram_type` and at least one node
- **THEN** it passes the IR boundary

#### Scenario: An invalid diagram is rejected
- **WHEN** a `diagram` block has an unknown `diagram_type` or no nodes
- **THEN** the IR boundary rejects it
