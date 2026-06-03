## Why

To run on real providers (DeepSeek, Xiaomi MiMo — both OpenAI-compatible), two practical gaps must
close: (1) easy multi-provider config without editing code, and (2) robustness to real-model output
(LLMs commonly wrap JSON in ```` ```json ```` fences or prose). This adds named provider profiles,
`.env` auto-loading, and JSON extraction so the IR boundary still accepts real output.

## What Changes

- `asa_providers`: **named OpenAI-compatible profiles** (`openai`, `deepseek`, `mimo`) with sensible
  default `base_url`/`model`, all overridable by env (`ASA_<NAME>_BASE_URL/_API_KEY/_MODEL`).
  `provider_from_env()` routes to a profile or `anthropic`. **No account-specific URL is committed**
  — those live in the user's gitignored `.env`.
- `asa_agents.outline`: **JSON extraction** — strip markdown fences / surrounding prose (take the
  outermost `{...}`) before the strict `from_llm_output` boundary.
- `asa-api`: **auto-load a local `.env`** (best-effort `python-dotenv`) so `python -m asa_api` picks
  up provider keys.

## Capabilities

### New Capabilities
- `provider-config`: named provider profiles + env/`.env` configuration + tolerance of real-model
  output formatting, so the service runs on real OpenAI-compatible providers with no code edits.

### Modified Capabilities
<!-- additive: existing llm-providers / outline-agent behavior is unchanged for the cases they cover -->

## Non-goals

- Per-request provider selection (env-level selection for MVP); retry/rate-limit policy.
- Committing any keys or account-specific endpoints (these stay in gitignored `.env`).

## Impact

- `asa-api` gains optional **`python-dotenv`** (BSD). No new required core deps.
- Real runs need a provider SDK (`packages/providers[openai]`) + keys in `.env`.
