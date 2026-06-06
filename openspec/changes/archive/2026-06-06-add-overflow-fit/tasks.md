## 1. Auto-fit

- [x] 1.1 `_fit_font(items, region_w, region_h, base, floor)` — CJK-aware line estimate, shrink to fit
- [x] 1.2 `render_bullets` renders at the fitted size

## 2. Tests

- [x] 2.1 Unit: dense/long bullets get a smaller font than sparse ones; never below the floor
- [x] 2.2 Full suite green
