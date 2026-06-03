## 1. Package setup

- [x] 1.1 Create `packages/providers/` package (`pyproject.toml`, `asa_providers/`)
- [x] 1.2 Optional extras: `[openai]`, `[anthropic]`, `[all]`; dev deps incl. `asa-agents`; record SDKs in `NOTICE`

## 2. OpenAI-compatible adapter

- [x] 2.1 `OpenAICompatibleLLM(model, api_key, base_url, temperature, client=None)` — lazy `openai` import
- [x] 2.2 `complete` builds system+user messages, returns `choices[0].message.content`; env fallback

## 3. Anthropic adapter

- [x] 3.1 `AnthropicLLM(model, api_key, max_tokens, temperature, client=None)` — lazy `anthropic` import
- [x] 3.2 `complete` passes system separately, joins `content[].text`; env fallback

## 4. Selection

- [x] 4.1 `provider_from_env()` picks by `ASA_LLM_PROVIDER` (default openai); unknown raises

## 5. Tests (offline)

- [x] 5.1 OpenAI adapter: mock client → correct messages + extracted content; no-system case
- [x] 5.2 Anthropic adapter: mock client → system separate + joined text blocks
- [x] 5.3 Both satisfy the `LLM` Protocol (runtime-checkable)
- [x] 5.4 `provider_from_env()` raises on unknown provider
- [x] 5.5 Live roundtrip test, self-skipped without API keys
