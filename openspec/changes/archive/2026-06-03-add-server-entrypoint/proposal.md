## Why

All pieces exist but the product is not yet runnable as one command with a real provider and real
formula rendering wired. This adds the default wiring + a uvicorn entrypoint so `python -m asa_api`
serves the whole pipeline, and proves the full HTTP flow produces a real `.pptx` with rendered
formulas (end-to-end with FakeLLM; a real paper run just needs an API key).

## What Changes

- Add `asa_api/server.py` — `build_default_app(*, llm=None, formula_renderer=None, out_dir=None) -> FastAPI`:
  defaults `llm` to `provider_from_env()` and `formula_renderer` to `MatplotlibFormulaRenderer()`
  (both lazily imported, so importing the module needs no provider SDK).
- Add `asa_api/__main__.py` — `python -m asa_api` runs uvicorn on `ASA_HOST`/`ASA_PORT`.
- Add deps to `asa-api`: `uvicorn` (BSD), `asa-formula`, `asa-providers` (local).
- README "Run the server" section (env vars + real-paper run instructions).

## Capabilities

### New Capabilities
- `server`: a runnable default app wiring (real formula renderer + env-selected provider) and a
  `python -m asa_api` uvicorn entrypoint.

### Modified Capabilities
<!-- composes api + llm-providers + formula-rendering; no spec change there -->

## Non-goals

- Production hardening (workers, TLS, durable store), Docker — later.
- A live real-LLM test in CI (needs keys); the end-to-end test uses FakeLLM with real rendering.

## Impact

- `asa-api` gains `uvicorn` (BSD) + `asa-formula`/`asa-providers` (local). All permissive.
- Running on a real paper requires the user to install a provider extra and set `ASA_*` env keys.
