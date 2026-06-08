## Why

The MiMo gateway key is dead (401) and the project no longer uses MiMo. Remove the `mimo` profile so
the supported providers are exactly `openai` and `deepseek` (plus `anthropic`), and the env-override
example is illustrated with a profile we actually use.

## What Changes

- Remove the built-in `mimo` profile from `_OPENAI_PROFILES` (and its mention in docstrings).
- Retarget the env-override test and spec scenario from `mimo` to `deepseek`.
- Strip `ASA_MIMO_*` keys from local `.env` (gitignored); set `ASA_LLM_PROVIDER=deepseek`.
- Archived OpenSpec changes that mention MiMo are immutable history and are left untouched.

## Capabilities

### Modified Capabilities
- `provider-config`: supported built-in profiles are `openai` and `deepseek` (MiMo removed).

## Impact

- `profiles.py`, `providers/__init__.py`, `test_providers.py`, `docs/SPEC.md`, local `.env`.
  Account-specific endpoints still come from env (`ASA_<NAME>_BASE_URL`). Suite green.
