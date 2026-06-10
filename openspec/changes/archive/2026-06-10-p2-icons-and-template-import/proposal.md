## Why

P2 wave of paper-ppt-agent-inspired polish: concept icons lift card/stat readability (their decks use
a curated icon corpus with a strict density policy), and users need to bring their own .pptx template
(lab/institution identity) instead of being limited to the two built-in styles.

## What Changes

- **Icon system**: Tabler icons (MIT, from upstream npm `@tabler/icons`) rendered to tinted PNGs by a
  new Node/resvg sidecar (`icon_render.js` + `IconRenderer`, cached, absolute-path safe). A closed
  ~44-name `ICON_WHITELIST`; unknown names skip silently (omit-over-decorate). `CalloutBlock.icon` +
  `StatItem.icon` IR fields; compiler renders via an injectable `icon_resolver`; planner prompt lists
  the whitelist with a ≤2-per-slide policy; server wires `default_icon_renderer`.
- **Template import**: `POST /templates` accepts a .pptx, deterministically extracts theme tokens
  (major fonts, accent1-6 palette) into a registered custom StyleProfile whose `base_template` points
  at the file — compiling with it inherits the real master natively. Profiles persist as JSON and
  rehydrate at startup; `GET /templates` lists them; the frontend style picker gains custom entries +
  an import button.

## Capabilities

### Modified Capabilities
- `slide-ir`: icon fields on callout/stat.
- `pptx-compiler`: icon rendering; style registration; base_template master inheritance; theme extraction.
- `formula-rendering`: icon sidecar (shares the Node/resvg runtime).
- `api`: /templates endpoints + rehydration.

## Impact

7 new tests (icon render/skip, sidecar smoke, extract+register, master inheritance, dict roundtrip,
endpoint roundtrip incl. a full run with an imported style). All licenses clean (Tabler MIT from
upstream; resvg stays arms-length).
