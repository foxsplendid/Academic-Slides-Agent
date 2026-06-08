## 1. Remove MiMo

- [x] 1.1 Drop `mimo` from `_OPENAI_PROFILES` + docstrings
- [x] 1.2 Retarget env-override test to `deepseek`
- [x] 1.3 Update `docs/SPEC.md` + strip `ASA_MIMO_*` from local `.env`

## 2. Verify

- [x] 2.1 `provider_from_env('mimo')` now raises; deepseek/openai/anthropic intact; suite green
