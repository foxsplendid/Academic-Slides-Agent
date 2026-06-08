## MODIFIED Requirements

### Requirement: Named OpenAI-compatible profiles
The system SHALL provide named profiles (at least `openai` and `deepseek`) that resolve a
`base_url`, `model`, and `api_key` from sensible defaults overridable by environment variables
(`ASA_<NAME>_BASE_URL`, `ASA_<NAME>_API_KEY`, `ASA_<NAME>_MODEL`).

#### Scenario: Profile resolves with env override
- **WHEN** `ASA_DEEPSEEK_API_KEY` is set and the `deepseek` profile is resolved
- **THEN** it yields the DeepSeek base URL, a model, and that API key

#### Scenario: Account-specific endpoint comes from env, not code
- **WHEN** `ASA_DEEPSEEK_BASE_URL` is set
- **THEN** the resolved `deepseek` profile uses that base URL instead of the built-in default
