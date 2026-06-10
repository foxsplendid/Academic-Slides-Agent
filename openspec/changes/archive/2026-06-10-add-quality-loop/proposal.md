## Why

Nothing in the pipeline ever *saw* a rendered slide: a schema-perfect deck could still be visually
broken (crammed text, sliver figures). Research consensus (Paper2Poster, DeepPresenter ablations)
says render-grounded checks with a CLOSED defect taxonomy are the proven lever — while free-form
VLM "make it prettier" critique is unreliable (Design2Code).

## What Changes

- **Deterministic geometry lint** (`pptx_compiler.lint_compiled_deck`): exact, AI-free post-compile
  checks — text auto-shrunk to the 10pt floor, figure-led slides whose largest picture renders below
  10% of the slide, content-shape overlap. Findings are repair-routable (`slide '<id>': ...`).
- **Quality loop in the critic node**, cheapest first: IR checks → (when clean) compile a throwaway
  render and geometry-lint it → (when clean, opt-in) VLM visual critique. All stages fail open.
- **VLM visual critic** (`asa_agents.visual_critic`, opt-in via `ASA_VLM_CRITIC` + optional
  `ASA_VLM_MODEL`): renders the deck (LibreOffice headless → pypdfium2; PowerPoint COM fallback on a
  dev box), asks a vision model to confirm ONLY a closed taxonomy (text_overflow, element_overlap,
  figure_too_small, slide_too_dense, slide_too_empty) and emit IR-level suggestions; findings join
  the same bounded repair loop. `OpenAICompatibleLLM` gains `complete_vision`.

## Capabilities

### Modified Capabilities
- `critic`: geometry lint + closed-taxonomy visual critique.
- `orchestration`: the critic node runs the staged quality loop; `build_graph(vision_llm=…)`.

## Impact

6 new tests (lint: crammed/tiny-figure/clean; visual: id mapping + taxonomy filter, renderer-absent
skip, garbage-output fail-open). Suite green. Default behavior unchanged unless ASA_VLM_CRITIC is set
(lint is free and always on).
