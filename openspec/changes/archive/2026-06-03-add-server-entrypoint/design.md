## Context

`create_app(llm, ...)` exists but requires callers to assemble the LLM + formula renderer. This adds
a one-call default wiring and a uvicorn entrypoint so the product runs with one command.

## Goals / Non-Goals

**Goals:**
- `build_default_app` defaulting to `provider_from_env()` + `MatplotlibFormulaRenderer()`.
- `python -m asa_api` uvicorn entrypoint; end-to-end proof producing a real `.pptx` with formulas.

**Non-Goals:**
- Prod hardening, Docker, live-LLM CI test.

## Decisions

- **Lazy imports inside `build_default_app`** — provider SDK and matplotlib are imported only when
  their defaults are actually used, so the module imports cheaply and tests inject a `FakeLLM`
  without any provider SDK.
- **Default formula renderer = matplotlib** — real formulas render out of the box; the deck the user
  downloads shows pictures, not raw LaTeX.
- **Env config** — `ASA_HOST`/`ASA_PORT`/`ASA_OUT_DIR`; provider via `ASA_LLM_PROVIDER` + keys.
- **uvicorn as a runtime dep of `asa-api`** — it is the serving runtime; kept out of `core`.

## Risks / Trade-offs

- [Real-paper run is untestable here without keys] → the end-to-end test uses FakeLLM but exercises
  real ingestion + graph + compile + formula rendering, producing a genuine `.pptx`. The README
  documents the one-key step to run on a real paper.
- [Starting uvicorn in a test would block] → tests target `build_default_app` + the module's `main`
  callable, not a live server.
