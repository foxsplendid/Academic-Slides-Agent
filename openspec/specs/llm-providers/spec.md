# llm-providers Specification

## Purpose
TBD - created by archiving change add-llm-providers. Update Purpose after archive.
## Requirements
### Requirement: OpenAI-compatible adapter
`OpenAICompatibleLLM` SHALL implement `complete(prompt, *, system=None)` by issuing a Chat
Completions request (system + user messages) and returning the message content.

#### Scenario: Builds messages and extracts content
- **WHEN** `complete("p", system="s")` is called
- **THEN** the request carries a system message then a user message, and the returned string is the response content

#### Scenario: Omits system when not given
- **WHEN** `complete("p")` is called with no system
- **THEN** the request carries only a user message

### Requirement: Anthropic adapter
`AnthropicLLM` SHALL implement `complete(prompt, *, system=None)` by issuing a Messages request
(system passed separately) and returning the concatenated text blocks.

#### Scenario: Builds request and joins text blocks
- **WHEN** `complete("p", system="s")` is called
- **THEN** the request carries the system separately and a user message, and the result joins the response's text blocks

### Requirement: Conform to the LLM Protocol
Both adapters SHALL satisfy the `LLM` Protocol so they are usable anywhere a fake is.

#### Scenario: Adapters are LLM instances
- **WHEN** an adapter instance is checked against the `LLM` runtime-checkable Protocol
- **THEN** it is recognized as an `LLM`

### Requirement: Optional, lazily-imported SDKs
The provider SDKs SHALL be optional and imported lazily, so importing `asa_providers` requires no
SDK; a client may be injected for testing.

#### Scenario: Package imports without SDKs and accepts an injected client
- **WHEN** `asa_providers` is imported and an adapter is constructed with `client=<mock>`
- **THEN** no provider SDK import is required and `complete` uses the injected client

### Requirement: Key/config via constructor or environment
Configuration SHALL come from constructor arguments or environment variables, never hardcoded.

#### Scenario: Unknown provider selection raises
- **WHEN** `provider_from_env()` runs with an unsupported `ASA_LLM_PROVIDER`
- **THEN** it raises a clear error

### Requirement: Optional output-token cap
The OpenAI-compatible adapter SHALL accept an optional `max_tokens` (constructor or `ASA_MAX_TOKENS`)
and SHALL pass it to the completion request only when set, leaving default behavior unchanged otherwise.

#### Scenario: max_tokens forwarded only when configured
- **WHEN** `max_tokens` is set
- **THEN** the completion request includes it
- **WHEN** it is unset
- **THEN** the request omits it

