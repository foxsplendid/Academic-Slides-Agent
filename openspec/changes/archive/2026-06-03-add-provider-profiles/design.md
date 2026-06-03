## Context

The product runs on the `LLM` Protocol with OpenAI-compatible + Anthropic adapters. To use real
providers (DeepSeek, MiMo) we need code-free multi-provider config and robustness to real output.

## Goals / Non-Goals

**Goals:**
- Named profiles resolvable from env; `.env` auto-load; JSON extraction before the IR boundary.

**Non-Goals:**
- Per-request provider choice; retry/backoff; committing keys or account-specific URLs.

## Decisions

- **Profiles are a small dict** `{name: {base_url, default_model}}`; resolution overlays env
  (`ASA_<NAME>_BASE_URL/_API_KEY/_MODEL`). Built-in defaults are generic public endpoints; the user's
  specific MiMo gateway lives in `.env` via `ASA_MIMO_BASE_URL` — **never committed**.
- **`resolve_openai_profile(name) -> dict` is pure** (no client construction) so it is unit-testable
  offline; `provider_from_env` constructs the adapter from it.
- **JSON extraction takes the outermost `{...}`** — simple and robust to ```` ```json ```` fences and
  surrounding prose. The strict `from_llm_output` boundary still validates; output with no object
  still fails (no `{}` → unchanged behavior).
- **`.env` auto-load is best-effort** — if `python-dotenv` is absent or no `.env` exists, startup
  proceeds. Keeps tests/CI unaffected.

## Risks / Trade-offs

- [Real model emits invalid IR despite the prompt] → extraction handles formatting, not semantics;
  a genuinely malformed deck still fails the boundary (correctly). Prompt tuning is iterative.
- [Outermost-brace extraction could grab too much if prose contains braces] → acceptable for MVP;
  the boundary rejects non-decks. A JSON-aware extractor can replace it later.
- [Keys in `.env`] → `.env` is gitignored; resolution reads env only; nothing secret is committed.
