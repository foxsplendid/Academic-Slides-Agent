## ADDED Requirements

### Requirement: Optional output-token cap
The OpenAI-compatible adapter SHALL accept an optional `max_tokens` (constructor or `ASA_MAX_TOKENS`)
and SHALL pass it to the completion request only when set, leaving default behavior unchanged otherwise.

#### Scenario: max_tokens forwarded only when configured
- **WHEN** `max_tokens` is set
- **THEN** the completion request includes it
- **WHEN** it is unset
- **THEN** the request omits it
