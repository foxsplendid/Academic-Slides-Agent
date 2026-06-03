## 1. State extension

- [x] 1.1 Add `tables: list[TableBlock]` and `output_path: Optional[str]` to `GenerationState` (slide-ir, additive)

## 2. Dependencies

- [x] 2.1 Add `langgraph` (Apache-2.0) + `asa-pptx-compiler` (local) to `asa-agents`; record langgraph in `NOTICE`

## 3. Graph

- [x] 3.1 `plan` node — outline agent (LLM → IR boundary) → slides/outline, phase `AWAIT_OUTLINE_APPROVAL`
- [x] 3.2 `approval` node — `interrupt({"outline": ...})`; apply approval/edits → phase `MAPPING`
- [x] 3.3 `compile` node — render deck → `.pptx`, set `output_path`, phase `DONE`
- [x] 3.4 `build_graph(llm, *, formula_renderer=None, out_dir="exports", checkpointer=None)` → compiled StateGraph

## 4. Tests

- [x] 4.1 Full run (invoke → interrupt → resume) writes a `.pptx` at `output_path`
- [x] 4.2 First invoke pauses at the interrupt and writes no `.pptx`
- [x] 4.3 Resume with approval completes and records approval/edits
- [x] 4.4 Streaming emits at least one per-node update
- [x] 4.5 Non-IR LLM output aborts in `plan`; no `.pptx` written
