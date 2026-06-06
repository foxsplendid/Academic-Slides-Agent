## Why

We want a template system, but the reference look (the user's 组会 deck) is **per-shape manual
formatting, not a master/theme** — so "inherit a .pptx master" can't capture it. The portable way to
capture and swap an academic look is a **style profile**: the design tokens (fonts, sizes, colors,
emphasis) the compiler applies. Today those tokens are hardcoded; this makes them a selectable profile
(the current values become the `academic` profile = the user's tokens), so the look is swappable and,
later, editable to the user's refined style.

## What Changes

- **`StyleProfile`** (`pptx_compiler/style.py`): EA/Latin fonts, title/body/caption sizes, emphasis
  color, diagram node colors, widescreen flag. `ACADEMIC` profile = the current (user-derived) tokens,
  so default output is unchanged. A second profile proves swapping changes the look.
- **Thread `style` through the compiler** (`compile_deck(style=…)` → block/diagram renderers); defaults
  to `ACADEMIC` so existing calls/tests are byte-for-byte compatible.
- **Selectable**: `compile_deck` also keeps the optional `template=` .pptx base (master/theme) for when
  a master-based template exists. The graph/server pass a profile chosen by `ASA_STYLE`.

## Capabilities

### Modified Capabilities
- `pptx-compiler`: a selectable `StyleProfile` parameterizes fonts/sizes/colors (default `ACADEMIC`),
  plus the existing optional `.pptx` base template.

## Non-goals

- Authoring a master/theme `.pptx` template (the user's style isn't master-based). A template
  marketplace / per-layout placeholder binding. Importing PPT-Agent's HTML/SVG layouts (AGPL,
  incompatible).

## Impact

- New `pptx_compiler/style.py`; `compiler.py`/`blocks.py`/`diagram.py` read tokens from `style`;
  `graph.py`/`app.py`/`server.py` thread a profile (`ASA_STYLE`). No IR change, no new deps. Verified:
  the same deck under two profiles renders different fonts/colors; default is unchanged.
