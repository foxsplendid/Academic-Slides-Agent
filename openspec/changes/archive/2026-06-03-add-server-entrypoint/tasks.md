## 1. Default wiring

- [x] 1.1 `asa_api/server.py` — `build_default_app(*, llm=None, formula_renderer=None, out_dir=None)` with lazy defaults (`provider_from_env`, `MatplotlibFormulaRenderer`)

## 2. Entrypoint

- [x] 2.1 `asa_api/__main__.py` — `main()` builds the default app and runs uvicorn on `ASA_HOST`/`ASA_PORT`

## 3. Dependencies & docs

- [x] 3.1 Add `uvicorn` (BSD) + `asa-formula` + `asa-providers` to `asa-api`; record uvicorn in `NOTICE`
- [x] 3.2 README "Run the server" section (env vars + real-paper run)

## 4. Tests & real run

- [x] 4.1 `build_default_app(llm=<fake>)` returns an app without importing a provider SDK
- [x] 4.2 End-to-end (create -> stream -> approve -> download) yields a `.pptx` with a formula picture
- [x] 4.3 `asa_api.__main__` exposes a callable `main`
- [x] 4.4 Run the end-to-end once for real and confirm a valid `.pptx` is produced
