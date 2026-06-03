## 1. Deterministic critic

- [x] 1.1 `asa_agents/critic.py` — `critique_deck(slides, evidence) -> list[str]` pure function
- [x] 1.2 Checks: empty/oversized title, empty content slide, bullet/table overflow, layout↔block mismatch, dangling figure asset_id
- [x] 1.3 Thresholds as module constants

## 2. Planner feedback

- [x] 2.1 `outline.py`: `build_outline(..., feedback=None)` appends prior findings to the prompt

## 3. Retry loop in the graph

- [x] 3.1 `graph.py`: add `critic` node (sets `critic_findings`, `phase=CRITIQUING`)
- [x] 3.2 `plan` consumes `state.critic_findings` as feedback and increments `retry_count` on retries
- [x] 3.3 Conditional edge: findings & `retry_count < max_retries` -> `plan`, else -> `approval`

## 4. Tests

- [x] 4.1 `critique_deck` flags each defect class and passes a clean deck
- [x] 4.2 Graph loops then proceeds: a defect-injecting FakeLLM that self-corrects after feedback reaches `approval`
- [x] 4.3 Budget exhaustion: a never-correcting FakeLLM stops after `max_retries` and still reaches `approval` with residual findings
- [x] 4.4 Full suite green
