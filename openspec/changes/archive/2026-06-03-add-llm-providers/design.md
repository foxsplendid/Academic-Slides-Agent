## Context

The `LLM` Protocol (asa_agents) is the seam. This change implements two real adapters while keeping
the rest of the system provider-agnostic and the test suite offline.

## Goals / Non-Goals

**Goals:**
- `OpenAICompatibleLLM` + `AnthropicLLM` implementing `complete(prompt, *, system=None) -> str`.
- Env-based key management; optional/lazy SDKs; offline mock tests + self-skipping live test.

**Non-Goals:**
- Token streaming; retry/backoff; auto-wiring the API; embeddings/tools.

## Decisions

- **One OpenAI-compatible adapter covers many providers.** The `openai` SDK targets OpenAI, DeepSeek,
  aggregators, and local Ollama/vLLM via `base_url` — maximal coverage from one class.
- **SDKs are optional extras (`[openai]`/`[anthropic]`/`[all]`) and imported lazily** inside the
  constructor — `import asa_providers` never requires a SDK, keeping the core install slim.
- **`client=` injection** — adapters accept a pre-built client so unit tests use a mock (no network,
  no SDK). The constructor only imports the SDK when it must build a real client.
- **Env fallback** — `ASA_OPENAI_API_KEY/BASE_URL/MODEL`, `ASA_ANTHROPIC_API_KEY/MODEL`,
  `ASA_LLM_PROVIDER`. Keys never hardcoded; `.env`-style usage is gitignored.
- **Non-streaming `complete`** — node-level streaming already exists in the graph; token streaming
  is a later enhancement behind the same interface.
- **Separate `packages/providers/` package** — keeps the heavy/optional SDKs out of `asa-agents`.

## Risks / Trade-offs

- [Provider response shapes differ] → adapters normalize: OpenAI `choices[0].message.content`;
  Anthropic joins `content[].text`. Covered by mock tests.
- [Live behavior untestable in CI] → live test self-skips without keys; mock tests assert the
  request/normalization contract.
- [SDK version drift] → pinned floors (`openai>=1`, `anthropic>=0.40`); lazy import isolates them.
