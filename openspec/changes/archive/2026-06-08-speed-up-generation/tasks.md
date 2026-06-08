## 1. Latency levers

- [x] 1.1 `EXPAND_SYSTEM` concise ceilings (notes 3–4 句, one-sentence bullets)
- [x] 1.2 `OpenAICompatibleLLM` `max_tokens` (ctor + `ASA_MAX_TOKENS`), default unset
- [x] 1.3 `build_deck_detailed` reads `ASA_EXPAND_WORKERS`; adaptive evidence cap
- [x] 1.4 `ASA_DEBUG_TIMING` emits `timing` event (wall vs sum → concurrency)

## 2. Tests

- [x] 2.1 max_tokens forwarded only when set
- [x] 2.2 adaptive cap bounds the expand prompt
- [x] 2.3 `ASA_EXPAND_WORKERS` caps in-flight expansions; suite green
