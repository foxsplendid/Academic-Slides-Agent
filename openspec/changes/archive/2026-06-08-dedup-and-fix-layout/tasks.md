## 1. Dedup + layout backstop

- [x] 1.1 `_dedup_plans` (difflib title+focus, CJK-safe) in skeleton pre-expansion
- [x] 1.2 `_fix_structural_layout` at assembly (divider+content → bullet_evidence)
- [x] 1.3 SKELETON/EXPAND prompt rules (anti-redundancy + divider semantics)

## 2. Critic

- [x] 2.1 Divider-with-content finding (repair-routable)
- [x] 2.2 Near-duplicate-title finding (human-facing, NOT repair-routable)

## 3. Tests

- [x] 3.1 dedup drops near-dup / keeps distinct / dropped plan not expanded
- [x] 3.2 relayout at assembly; real divider untouched
- [x] 3.3 critic findings; suite green
