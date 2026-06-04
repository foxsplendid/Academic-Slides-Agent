## 1. IR

- [x] 1.1 `ChartBlock` + `ChartSeries` (bar/line/scatter/pie); add to `Block` union; export; regenerate schema
- [x] 1.2 IR test: ChartBlock validates; unknown chart_type / empty series rejected

## 2. Compiler

- [x] 2.1 `render_chart`: CategoryChartData (bar/line/pie) + XyChartData (scatter) via `add_chart`
- [x] 2.2 Defensive: pad/truncate series to category count; title + legend
- [x] 2.3 Wire into `_render_block`; add `chart` to `_BLOCK_WEIGHT`
- [x] 2.4 Compiler test: a chart block renders a native chart (GraphicFrame.has_chart)

## 3. Planner

- [x] 3.1 Describe `ChartBlock` in the expand + single-shot prompts; **no-fabrication** rule (data must be in evidence)

## 4. Verify

- [x] 4.1 Full suite green; schema artifact updated
- [x] 4.2 Real run: planner emits a native chart from evidence data where appropriate
