## ADDED Requirements

### Requirement: Default app wiring
`build_default_app` SHALL construct the API app with a real formula renderer and an LLM that is
either injected or selected from the environment, importing provider SDKs lazily.

#### Scenario: Default app built with an injected LLM needs no provider SDK
- **WHEN** `build_default_app(llm=<fake>)` is called
- **THEN** it returns a FastAPI app without importing any provider SDK

### Requirement: End-to-end produces a deck with rendered formulas
The full HTTP flow (create -> stream -> approve -> download) on the default app SHALL produce a
`.pptx` in which formula blocks are embedded as rendered pictures.

#### Scenario: Downloaded deck contains a formula picture
- **WHEN** a deck containing a formula is generated end-to-end through the default app
- **THEN** the downloaded `.pptx` contains at least one picture shape (the rendered formula)

### Requirement: Server entrypoint
A `python -m asa_api` entrypoint SHALL exist that serves the default app via uvicorn.

#### Scenario: Module entrypoint is runnable
- **WHEN** `asa_api.__main__` is imported
- **THEN** it exposes a callable `main` that builds and serves the default app
