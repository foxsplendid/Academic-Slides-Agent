## Why

Blind-gate round 1 (Design gap 0.625) attributed our deficit to bare covers/dividers, missing chrome
and monotony. Theme v2 shipped those fixes; round 2 (same protocol, fresh judges) then surfaced a
regression the structure-page mandate introduced — structure pages ate the page budget (6/12 slides
structural, thin results chapters with no figures) — plus a bullets-overflow-into-callout defect and
terminology drift. Gap widened to 0.75; both rounds unanimously preferred the reference system.

## What Changes

- **Theme v2**: `SlideIR.subtitle` (cover meta line / content kicker 导读句 / divider lead-in);
  section breadcrumb footer; enriched cover/section/ending rendering; skeleton mandates 3-5 section
  dividers consistent with the TOC.
- **Round-2 regression fixes**: detail page budgets now count CONTENT pages (structure pages
  explicitly excluded); every results/validation/discussion chapter must carry at least one
  figure/chart page; bullets fit-estimation gains an 8% bottom safety margin (no more spill into the
  callout below); core-terminology consistency rule (hygrometer ≠ 温度计).

## Capabilities

### Modified Capabilities
- `slide-ir`: subtitle field.
- `pptx-compiler`: subtitle/kicker/breadcrumb rendering; fit margin.
- `outline-agent`: content-page budgets, chapter figure coverage, terminology rule.

## Impact

Gate record (Lin paper, 4 blind judges/round, PPTEval): R1 ours 3.88/2.88/4.00 vs theirs
4.38/3.50/4.63 (Design gap 0.625); R2 ours 3.50/2.75/3.50 vs theirs 4.50/3.50/4.75 (gap 0.75).
Per the pre-agreed criterion (gap > 0.5 after the Theme-v2 retest), **Path B is triggered**.
