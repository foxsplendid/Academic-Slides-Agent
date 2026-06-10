## Why

Bullets were flat (no nesting, fake '• ' prefix without hanging indent) and the IR had no way to
express a takeaway band or key-number cards — compositions every good academic deck uses.

## What Changes

- **Nested bullets**: `BulletBlock.items` accepts `str | BulletItem{text, children}` (one level).
  The renderer now emits REAL PowerPoint bullet formatting (buChar glyphs per level + hanging
  indent via marL/indent), so wrapped lines align correctly.
- **`CalloutBlock`** (label + text): a tinted takeaway card with an accent edge; the planner may use
  it instead of the final "→ " interpretation bullet.
- **`StatBlock`** (1-4 `StatItem{value,label}`): big-number cards in a row (value in accent color,
  label muted) for results/metrics slides; values must come from evidence.
- Planner vocabulary, render_md, content-type sets, critic bullet checks updated for the new shapes.

## Capabilities

### Modified Capabilities
- `slide-ir`: BulletItem nesting, CalloutBlock, StatBlock.
- `pptx-compiler`: real bullet formatting; callout + stat renderers.
- `outline-agent`: block vocabulary for callout/stat/nesting.

## Impact

3 new unit tests + suite green. The checkpointer's msgpack allowlist picks the new models up
automatically (it introspects the slide_ir module).
