## 1. Outline agent (content)

- [x] 1.1 Rewrite `SYSTEM_PROMPT`: Chinese 组会 output; method-paper narrative; concise one-line titles; per-slide interpretation; speaker notes; keep terms/symbols/citations original
- [x] 1.2 Figure grounding: prompt lists available figure asset_ids; reference figures ONLY from that list, else describe as text
- [x] 1.3 `**…**` emphasis convention (one key term/number per bullet)
- [x] 1.4 `build_outline_prompt` passes available figure asset_ids

## 2. Compiler (look)

- [x] 2.1 Fresh decks render 16:9 (13.333×7.5in)
- [x] 2.2 CJK-aware font helper (East-Asian 黑体 + Latin Times New Roman); title 28 / body 16 / caption 12
- [x] 2.3 `**…**` spans → bold red (FF0000) runs in bullets and titles

## 3. Ingestion (clean inputs)

- [x] 3.1 Two-column-aware PDF text (detect gutter, crop columns)
- [x] 3.2 Drop low-quality tables (no data rows, <2 cols, or majority auto-named `colN`)
- [x] 3.3 Widen evidence digest budget in `_evidence_digest`

## 4. Verify on the real paper

- [x] 4.1 Re-run Zhang 2026 PDF with MiMo: Chinese deck, concise titles, notes present, no dangling figure refs, critic clean
- [x] 4.2 Compiled .pptx is 16:9 with CJK fonts and red emphasis
- [x] 4.3 Full unit suite still green
