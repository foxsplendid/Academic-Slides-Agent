## Why

The biggest gap vs. reference agents (paper-ppt-agent) is visual **logic diagrams** — process steps,
comparisons, causal/relationship structures — which papers are full of and which we currently flatten
into bullets. Those agents make the **LLM emit SVG with absolute coordinates**, then need a heavy
geometry+VLM Critic loop to fix the LLM's misalignments. Our architecture locks the LLM to Slide-IR,
so we do it **better**: the LLM emits a *semantic* diagram (nodes + edges + type, **no coordinates**),
and a **deterministic layout engine** computes geometry → native, editable PowerPoint shapes. No
coordinate hallucination, no VLM needed, fully unit-testable. Asking for the diagram also forces the
planner to structure the paper's logic (improving content, not just layout).

## What Changes

- **New `DiagramBlock` in Slide-IR**: `diagram_type` ∈ flow/tree/cycle/comparison/pyramid/timeline,
  `nodes: [{id, label}]`, `edges: [{source, target, label?}]`, optional `title`. Added to the block
  union (locked vocabulary).
- **Deterministic layout engine + native render** (`pptx_compiler/diagram.py`): per type, compute node
  boxes + connectors and emit `add_shape(ROUNDED_RECTANGLE)` + `add_connector` (with arrowheads) +
  text — all native/editable. No image.
- **Planner awareness**: prompts describe `DiagramBlock` and when to use it (the paper has a
  process/comparison/causal structure), with **no fabricated relationships**.
- **Critic**: flag an edge whose `source`/`target` is not a defined node id.

## Capabilities

### Modified Capabilities
- `slide-ir`: add `DiagramBlock` (+ `DiagramNode`/`DiagramEdge`).
- `pptx-compiler`: deterministic diagram layout → native shapes/connectors.
- `outline-agent`: emit diagrams from the paper's logical structure (no fabrication).
- `critic`: validate diagram edge references.

## Non-goals

- Semantic-icon RAG (icon library + embeddings), freeform/custom topologies (SVG escape hatch), and a
  VLM aesthetic critic — later. v1 is pure-shape, six common academic diagram types.

## Impact

- `slide_ir/models.py` (+ schema), `pptx_compiler` (`diagram.py` + wiring + weight), `asa_agents`
  prompts + `critic.py`. No new deps. Verified: each diagram type renders native shapes; planner emits
  a diagram from real evidence.
