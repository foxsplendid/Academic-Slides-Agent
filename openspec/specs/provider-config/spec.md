# provider-config Specification

## Purpose
TBD - created by archiving change add-provider-profiles. Update Purpose after archive.
## Requirements
### Requirement: Named OpenAI-compatible profiles
The system SHALL provide named profiles (at least `openai`, `deepseek`, `mimo`) that resolve a
`base_url`, `model`, and `api_key` from sensible defaults overridable by environment variables
(`ASA_<NAME>_BASE_URL`, `ASA_<NAME>_API_KEY`, `ASA_<NAME>_MODEL`).

#### Scenario: Profile resolves with env override
- **WHEN** `ASA_DEEPSEEK_API_KEY` is set and the `deepseek` profile is resolved
- **THEN** it yields the DeepSeek base URL, a model, and that API key

#### Scenario: Account-specific endpoint comes from env, not code
- **WHEN** `ASA_MIMO_BASE_URL` is set
- **THEN** the resolved `mimo` profile uses that base URL instead of the built-in default

### Requirement: Environment-selected provider
`provider_from_env()` SHALL build an adapter selected by `ASA_LLM_PROVIDER` — a known OpenAI
profile or `anthropic` — and raise for an unknown value.

#### Scenario: Unknown provider raises
- **WHEN** `ASA_LLM_PROVIDER` is an unsupported value
- **THEN** `provider_from_env()` raises a clear error

### Requirement: Tolerate real-model output formatting
The outline agent SHALL extract the JSON object from the LLM response (ignoring markdown code
fences or surrounding prose) before the strict IR boundary, while still rejecting output with no
JSON object.

#### Scenario: Fenced JSON is accepted
- **WHEN** the LLM returns a valid Slide-IR Deck wrapped in a ```` ```json ```` fence
- **THEN** `build_outline` returns a `Deck`

#### Scenario: Output with no JSON is still rejected
- **WHEN** the LLM returns prose with no JSON object
- **THEN** `build_outline` raises an IR boundary error

### Requirement: Service loads a local .env
On startup the service SHALL best-effort load a local `.env` so provider keys are available without
manual exporting; a missing `.env` or missing dotenv library SHALL NOT fail startup.

#### Scenario: Missing .env does not fail
- **WHEN** the default app is built with no `.env` present
- **THEN** startup proceeds without error

