## 1. Two-stage builder

- [x] 1.1 `asa_agents/deepen.py`: skeleton stage -> slide plans (title, layout_type, focus, evidence_pages, figure_id)
- [x] 1.2 Expand stage: per slide, focused prompt with full evidence-page text + figure caption -> one SlideIR slide
- [x] 1.3 Assemble slides -> Deck through the IR boundary; reuse per-call JSON retry
- [x] 1.4 `build_deck_detailed(assets, tables, llm, *, feedback=None)` signature matches `build_outline`

## 2. Pluggable planner

- [x] 2.1 `build_graph(llm, *, planner=build_outline, ...)`; plan node calls `planner`
- [x] 2.2 `server.build_default_app` wires `planner=build_deck_detailed`

## 3. Tests & verify

- [x] 3.1 Unit: scripted FakeLLM (skeleton + N slide responses) -> deep Deck; bullets per slide > single-shot
- [x] 3.2 Unit: graph still works with default planner (unchanged)
- [x] 3.3 Real run: Zhang 2026 (MinerU) detailed deck — more substantive bullets + notes; full suite green
