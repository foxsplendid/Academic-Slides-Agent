## Why

A full constraint audit (3-layer sweep: prompts, IR+critic, compiler+ingestion) classified every rule
that limits model output. Verdict: ~20 protective constraints (anti-hallucination, schema validity,
geometry ownership) must stay; ~11 capacity quotas and ~10 taste rules were capping expression for no
quality benefit — including the page-count budget the user flagged.

## What Changes

- **Page count & density model-decided by default** ("auto" detail level, now the default): the model
  derives page count from the paper ("每个值得讲透的要点一页,讲透为准"); brief/normal/high remain as
  optional soft targets ("可按内容增减"). Bullets/notes quotas likewise content-driven in auto.
- **figure_ids list** replaces the scalar figure_id in the skeleton schema (figure_grid finally
  expressible end-to-end; legacy figure_id still accepted); expansion receives ALL assigned figures
  with caption hints (400 chars).
- **Figure-page layout un-collapsed**: expansion now follows the skeleton's planned figure layout
  (figure_caption/figure_left/big_figure/figure_grid) instead of forcing figure_caption.
- **Quotas → guidance**: per-bullet 60-char cap, subtitle 25-char cap, emphasis ≤3/page, icon ≤2/page,
  section-divider 3-5 count, "严禁连续4页" — all reworded as design coaching; narrative arc marked
  adjustable by paper type.
- **Evidence visibility raised**: planner digest 12k→24k (2.5k/page), expansion caps 3800/6000 →
  6000/9000; figure captions stored to 600 chars, menu hints to 200.
- **Open icon vocabulary**: any installed Tabler outline icon renders (directory check, fail-open);
  whitelist remains as examples/fallback.
- **Critic recalibrated**: MAX_BULLETS 7→9; layout-monotony findings advisory (reach the human, never
  burn the repair budget); StatBlock schema cap removed — >4 items is now a repairable finding.
- **Misc**: TOC wraps to two columns beyond 7 items (no silent truncation); MinerU OCR language via
  ASA_MINERU_LANG; ASA_TEMPERATURE env override; IR-retry error feedback 500→2000 chars.

## Capabilities

### Modified Capabilities
- `outline-agent`, `slide-ir`, `critic`, `pptx-compiler`: as above.

## Impact

226 tests green (assertions updated to the new contracts). Protective constraints unchanged:
provenance/no-fabrication rules, no-coordinates, IR boundary, junk filters, retry budgets.
