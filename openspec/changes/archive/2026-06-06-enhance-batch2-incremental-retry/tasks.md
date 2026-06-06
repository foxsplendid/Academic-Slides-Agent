## 1. Incremental repair

- [x] 1.1 `_bad_ids(feedback)` — parse flagged slide ids from critic findings
- [x] 1.2 `_repair_slide(slide, findings, llm)` — focused fix-this-slide call (preserve topic/evidence)
- [x] 1.3 `build_deck_detailed(*, prior_slides=None)`: when prior_slides + feedback, repair only flagged slides, keep the rest
- [x] 1.4 `build_outline` accepts a no-op `prior_slides`; graph passes `prior_slides` on retry

## 2. Tests & verify

- [x] 2.1 Unit: a single flagged slide triggers exactly one repair call; good slides are kept verbatim
- [x] 2.2 Full suite green
