## 1. IR

- [x] 1.1 `DiagramNode`, `DiagramEdge`, `DiagramBlock` (6 diagram_types); add to `Block` union; export; regen schema
- [x] 1.2 IR test: valid diagram accepted; unknown diagram_type / empty nodes rejected

## 2. Layout engine + render

- [x] 2.1 `pptx_compiler/diagram.py`: per-type layout (flow/comparison/cycle/tree/pyramid/timeline) → node boxes + connectors
- [x] 2.2 Native render: `add_shape(ROUNDED_RECTANGLE)` nodes + `add_connector` arrows + text; arrowheads
- [x] 2.3 Wire into `_render_block`; add `diagram` to `_BLOCK_WEIGHT`
- [x] 2.4 Compiler test: each type renders ≥ node-count shapes; flow renders connectors

## 3. Planner + critic

- [x] 3.1 Describe `DiagramBlock` in expand + single-shot prompts (no fabricated relationships)
- [x] 3.2 Critic: flag an edge referencing an undefined node id

## 4. Verify

- [x] 4.1 Full suite green; schema updated
- [x] 4.2 Real run: planner emits a native diagram from a paper's process/comparison structure
