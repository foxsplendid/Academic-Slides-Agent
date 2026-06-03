## Why

Everything runs on a `FakeLLM`; the only thing between a demo and running on a real paper is a
real provider. This adds two adapters implementing the `LLM` Protocol — covering essentially the
whole hosted + local ecosystem — with env-based key management and no required SDK at import time.

## What Changes

- Add `packages/providers/` (`asa_providers`):
  - **`OpenAICompatibleLLM`** — `openai` SDK against any Chat Completions endpoint (OpenAI, DeepSeek,
    aggregators, **local Ollama/vLLM**) via `base_url` + `api_key`.
  - **`AnthropicLLM`** — `anthropic` SDK (Claude).
  - **`provider_from_env()`** — pick an adapter by `ASA_LLM_PROVIDER`.
  - SDKs are **optional extras** (`[openai]`, `[anthropic]`, `[all]`) and **lazy-imported**, so the
    package imports without any SDK installed; a `client=` argument allows mock injection for tests.
- Config from constructor args with **env fallback** (`ASA_OPENAI_API_KEY/BASE_URL/MODEL`,
  `ASA_ANTHROPIC_API_KEY/MODEL`) — never hardcoded, never committed.

## Capabilities

### New Capabilities
- `llm-providers`: real adapters (OpenAI-compatible, Anthropic) for the `LLM` Protocol, with env
  key management and optional/lazy SDKs.

### Modified Capabilities
<!-- implements the existing LLM Protocol from asa_agents structurally; no spec change there -->

## Non-goals

- Token-level streaming from the LLM (node-level streaming already exists); non-streaming `complete` for MVP.
- Auto-wiring the API to a provider (a trivial follow-up; `provider_from_env()` is provided).
- Retry/backoff/rate-limit policy (later).

## Impact

- New package `packages/providers/`; **optional** deps `openai` (Apache-2.0) / `anthropic` (MIT) —
  both permissive. Core install pulls neither.
- Tests are offline (mock clients); a live test self-skips without API keys.
