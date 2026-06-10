## Why

The old frontend was a single-page wizard with a text-only outline approval — far from the
interaction quality of paper-ppt-agent's app (sidebar history, live progress, visual review). The
user asked for an independent redesign modeled on it, surfacing every implemented capability.

## What Changes

- **API**: per-job options on `/jobs/upload` (style_name, parser, split_figures, vlm_critic,
  native_formula — parser/split applied via env-scoped ingest; the rest ride GenerationState);
  `GET /jobs` history (meta.json persisted per job) + `DELETE /jobs/{id}`;
  `POST /jobs/{id}/preview` renders the current deck (final out.pptx, else a draft compile of the
  in-flight slides) to per-slide PNGs via the visual-critic renderer chain, served by
  `GET /jobs/{id}/preview/{idx}`; `download` falls back to the on-disk out.pptx (survives restarts);
  approval rejection re-streams over SSE (`/stream?reject=1&feedback=…`) so the replan progress is live.
- **Orchestration**: the approval node honors `approved=false` — the human's feedback becomes
  findings and the graph routes back to plan (a real reject→replan→re-approve loop); per-job
  style/options are read from state (style override, vlm_critic gate, native_formula renderer copy).
- **Web UI rewritten** (React 18 + Vite + TS + Tailwind + lucide-react + zustand, all MIT; no AGPL
  editor — export-first preserved): 3-view app shell — sidebar (history with status badges, open/
  delete, theme toggle), Generate view (drag-drop multi-file upload, config panel: style/parser/
  3 opt-in toggles, ingest stats, 7-stage progress with live per-slide counter + log), **visual
  approval view** (real rendered slide thumbnails + lightbox + approve / reject-with-feedback),
  Result view (final preview grid + download). Dual light/dark theme.

## Capabilities

### Modified Capabilities
- `api`: per-job options, history, preview rendering, reject-resume streaming, disk-fallback download.
- `orchestration`: approval rejection loop; per-job style/options from state.
- `web-ui`: 3-view app shell with visual approval.

## Impact

5 new API tests (history/delete, options reach state, preview 200-or-503 fail-open, reject→replan→
approve, approve 409 guard). Frontend builds clean (tsc + vite). GenerationState gains optional
`style` + `options` (additive).
