## 1. Package setup

- [x] 1.1 Create `packages/agents/` package (`pyproject.toml`, `asa_agents/`)
- [x] 1.2 Depend only on `asa-slide-ir` (local via `tool.uv.sources`); no LLM SDK

## 2. LLM seam

- [x] 2.1 `LLM` Protocol: `complete(prompt, *, system=None) -> str`
- [x] 2.2 `FakeLLM`: scripted responses + records `calls`

## 3. Outline agent

- [x] 3.1 `build_outline_prompt(assets, tables)` — compact, provenance-tagged evidence digest
- [x] 3.2 `SYSTEM_PROMPT` — academic structure + IR-only output rule + allowed vocabulary
- [x] 3.3 `build_outline(assets, tables, llm) -> Deck` via `from_llm_output` (IR boundary)

## 4. Hard-Stop workflow

- [x] 4.1 `plan_outline(state, assets, tables, llm)` → set slides/outline, phase `AWAIT_OUTLINE_APPROVAL`
- [x] 4.2 `approve_outline(state, *, edited_outline=None)` → approve, record edits, phase `MAPPING`

## 5. Tests

- [x] 5.1 Valid IR → Deck; non-IR → IR boundary error
- [x] 5.2 FakeLLM receives evidence + non-empty system instruction
- [x] 5.3 `plan_outline` pauses at `AWAIT_OUTLINE_APPROVAL` with populated slides
- [x] 5.4 `approve_outline` advances to `MAPPING` and records edits
- [x] 5.5 `FakeLLM` records calls and returns scripted responses in order
