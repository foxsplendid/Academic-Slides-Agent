## 1. Parallel expansion

- [x] 1.1 `build_deck_detailed(*, parallel=True, max_workers=6, progress=None)`: thread-pool expansion, results in plan order
- [x] 1.2 On any worker exception, fall back to full serial expansion
- [x] 1.3 `build_outline` accepts a no-op `progress=None` (planner-signature parity)

## 2. Progress plumbing

- [x] 2.1 Builder calls `progress({...})` for skeleton + each slide done/total
- [x] 2.2 Graph `plan` node wires `progress` to `get_stream_writer()` (guarded)
- [x] 2.3 SSE endpoint streams `["updates","custom"]`; emit `progress` events

## 3. Frontend

- [x] 3.1 `api.ts streamJob`: handle `progress` events (onProgress)
- [x] 3.2 `App.tsx`: phase stepper + live "N/total 页" counter; keep log collapsible
- [x] 3.3 styles for the status panel

## 4. Tests & verify

- [x] 4.1 Unit: parallel build returns slides in order; progress callback invoked with done/total
- [x] 4.2 Unit: a failing expansion triggers serial fallback and still returns a deck
- [x] 4.3 Frontend builds (`tsc` + `vite build`); full suite green; real run shows live progress
