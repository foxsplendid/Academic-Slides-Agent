## Why

A 12-slide / 13-figure paper took ~358s — ≈ 13 LLM calls × ~27.5s, i.e. fully serial throughput,
which means the gateway is likely serializing concurrent requests. We ship the depth-safe, guaranteed
wins (concise output, tunable concurrency, measurability) without touching per-slide depth.

## What Changes

- **Concise output ceilings** in `EXPAND_SYSTEM` (speaker_notes 3–4 句; one-sentence bullets, no
  over-elaboration). Fewer decode tokens per call — the guaranteed latency win regardless of concurrency.
- **`max_tokens`** on `OpenAICompatibleLLM` (ctor arg + `ASA_MAX_TOKENS`), default unset so behavior is
  unchanged; lets a deployment cap runaway decode without truncation risk.
- **Tunable concurrency**: `build_deck_detailed` reads `ASA_EXPAND_WORKERS` (default 6) instead of a
  hard-coded 6.
- **Concurrency probe**: `ASA_DEBUG_TIMING` emits a `timing` progress event (wall vs sum-of-calls →
  effective concurrency) so the gateway's real concurrency can be measured.
- **Adaptive evidence cap**: figure/table slides keep full 6000-char context; plain bullet slides
  (already focused by the skeleton) cap at ~3800.

## Capabilities

### Modified Capabilities
- `outline-agent`: tunable concurrency, adaptive evidence cap, concise output ceilings, timing probe.
- `llm-providers`: optional `max_tokens` cap.

## Impact

- `deepen.py`, `openai_compat.py`. No behavior change by default except concise output + adaptive cap
  (depth-safe). Verified: concurrency capped by env; adaptive cap bounds prompt; max_tokens forwarded
  only when set; full suite green.
