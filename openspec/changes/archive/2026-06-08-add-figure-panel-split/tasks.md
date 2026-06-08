## 1. Splitter

- [x] 1.1 `ingestion/panels.py split_composite` — Pillow band X-Y-cut, conservative gates, numpy-free
- [x] 1.2 MinerU emits sibling panel assets behind `ASA_SPLIT_FIGURES` (default off)

## 2. Tests

- [x] 2.1 Synthetic 2×2→4, 1×3→3; single-panel & small images don't split
- [x] 2.2 Opt-in gate: off→1 figure, on→1 parent + panels; suite green
