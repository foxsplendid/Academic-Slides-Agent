## Why

The user directed extracting PPT-Agent's `academic_defense` look as a scaffold to get the template flow
working (to be replaced later by a profile built from their own decks). Capturing it needs a slide-title
color (its hallmark is dark-blue titles), which our StyleProfile lacked.

## What Changes

- **`StyleProfile.title_rgb`** (optional; None = theme default) applied to slide/section/cover titles
  via a new `color` argument to `add_rich_text`. `ACADEMIC` keeps `title_rgb=None` → unchanged.
- **`PPTAGENT_ACADEMIC` profile** — design *tokens* (colors/fonts/sizes are facts; no code/markup
  copied) from PPT-Agent's `academic_defense` design spec: white bg, **dark-blue (#003366) titles**,
  **dark-red (#CC0000) emphasis**, blue (#0066CC) accents, 微软雅黑/Arial. Clearly marked TEMPORARY
  scaffold to be replaced by a user-derived profile.

## Capabilities

### Modified Capabilities
- `pptx-compiler`: a `title_rgb` token + a scaffold `pptagent_academic` profile.

## Non-goals

- Copying PPT-Agent's SVG layouts/code (only token values, which are facts). A master-based `.pptx`
  template. The user's own final profile (later).

## Impact

- `style.py` (`title_rgb` field + `PPTAGENT_ACADEMIC`), `blocks.py` (`add_rich_text` `color`),
  `compiler.py` (titles use `title_rgb`). Default unchanged; verified `pptagent_academic` renders
  dark-blue titles + dark-red emphasis.
