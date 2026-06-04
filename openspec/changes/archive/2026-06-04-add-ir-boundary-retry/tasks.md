## 1. Boundary retry

- [x] 1.1 `build_outline(..., max_attempts=3)`: on `IRBoundaryError`, re-ask with the error fed back; re-raise after budget
- [x] 1.2 A valid deck on attempt 1 makes exactly one LLM call (no regression)

## 2. Tests

- [x] 2.1 Malformed-then-valid FakeLLM: build_outline recovers and returns the deck
- [x] 2.2 Persistently non-IR FakeLLM: still raises `IRBoundaryError` after `max_attempts`
- [x] 2.3 Full suite green
