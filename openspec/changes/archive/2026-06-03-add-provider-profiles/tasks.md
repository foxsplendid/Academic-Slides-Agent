## 1. Provider profiles

- [x] 1.1 `asa_providers`: `_OPENAI_PROFILES` (openai/deepseek/mimo) with default base_url + model
- [x] 1.2 `resolve_openai_profile(name) -> dict` (pure: base_url/api_key/model from env overrides)
- [x] 1.3 `provider_from_env()` routes to a profile or `anthropic`; unknown raises

## 2. Robust JSON extraction

- [x] 2.1 `asa_agents.outline._extract_json(text)` — outermost `{...}` (strips fences/prose)
- [x] 2.2 `build_outline` runs the LLM output through `_extract_json` before `from_llm_output`

## 3. Service .env loading

- [x] 3.1 `asa-api` best-effort `python-dotenv` load on default-app build; record in `NOTICE`

## 4. Tests (offline)

- [x] 4.1 `resolve_openai_profile` for deepseek/mimo honors env overrides (base_url/key/model)
- [x] 4.2 `provider_from_env` unknown value raises
- [x] 4.3 `build_outline` accepts fenced JSON; still rejects prose-only
- [x] 4.4 Missing `.env` / missing dotenv does not fail default-app build

## 5. Real API run (operational, not committed)

- [x] 5.1 Write a gitignored `.env` with DeepSeek + MiMo keys (from the user's PPT-Agent .env)
- [x] 5.2 Install a provider SDK and make one real DeepSeek call end-to-end; produce a `.pptx`
