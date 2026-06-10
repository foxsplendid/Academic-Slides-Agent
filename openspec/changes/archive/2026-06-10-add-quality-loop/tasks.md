## 1. Geometry lint

- [x] 1.1 `lint_compiled_deck` (font-floor, tiny figure, overlap), repair-routable findings
- [x] 1.2 Critic node compiles a throwaway render + lints when IR checks are clean

## 2. VLM critic (opt-in)

- [x] 2.1 Renderer chain (soffice→pypdfium2; PowerPoint COM dev fallback)
- [x] 2.2 Closed-taxonomy critique -> IR-level findings; `complete_vision` on the OpenAI adapter
- [x] 2.3 `ASA_VLM_CRITIC`/`ASA_VLM_MODEL` wiring in the server; fails open

## 3. Tests

- [x] 3.1 lint: crammed text / tiny figure / clean deck
- [x] 3.2 visual: slide-id mapping + taxonomy filter; no-renderer skip; garbage fail-open
