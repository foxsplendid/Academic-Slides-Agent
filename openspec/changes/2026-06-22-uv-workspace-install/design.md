# Design — uv workspace install

## Approach (chosen): uv workspace

A single root `pyproject.toml` owns the workspace. It is a **virtual** project
(`[tool.uv] package = false`) — it is never built or installed; it only hosts:

- `[tool.uv.workspace]` `members` (globs) + `exclude` — the single source of truth for membership.
- `[tool.uv.sources]` mapping every `asa-*` name to `{ workspace = true }` — inherited by all
  members, so each member's `dependencies` resolve siblings from the workspace. Per-package
  `[tool.uv.sources]` blocks are therefore removed.
- `[dependency-groups] dev` — the shared test tooling, installed by `uv sync` by default.

Install is then `uv sync --all-packages` (CI adds `--locked`). One command, no list.

### Membership globs and exclusions

```
members = ["packages/core/*", "packages/ingestion", "packages/agents",
           "packages/providers", "packages/vendor/*", "apps/*"]
exclude = ["packages/core/mapper", "packages/core/tables", "apps/web"]
```

`packages/core/*` and `apps/*` auto-discover future Python packages. uv **errors** on a globbed
member without a `pyproject.toml`, so the three non-distributions are excluded explicitly:
`packages/core/mapper` and `…/tables` are empty placeholders for the future `add-template-mapper`
change; `apps/web` is the React frontend (an npm package). Adding a *new* Python package under
`packages/` or `apps/` needs no edit here.

### Extras: what is and isn't in the default install (license-critical)

`uv sync --all-packages` installs every member editable + the default `dev` group. It does **not**
enable optional extras unless asked. This is deliberate:

- ✅ **In:** the `openai` client — pulled via `asa-providers[openai]` in the `dev` group so the
  provider tests run (matches the old `providers[openai,dev]` CI install).
- ❌ **Out:** `asa-svg2pptx`'s `raster-fallback` extra (svglib **LGPL** + reportlab) — must stay
  isolated behind an optional boundary (SPEC §2 / NOTICE). `--all-extras` would pull it, so we never
  use that flag.
- ❌ **Out:** `asa-ingestion`'s `docling` extra (heavy: PyTorch + models) — optional Tier-2 backend.

Verified by the license gate (88 dists, no GPL/AGPL) and an explicit `uv pip list` check that
svglib / reportlab / docling are absent and openai is present.

### apps/api undeclared dependency

`apps/api` imports `pptx_compiler` (in `/templates` and `/preview`) but listed only `asa-agents`,
relying on it to drag `asa-pptx-compiler` in transitively. `asa-pptx-compiler` is now declared
directly, so the API no longer breaks if `asa-agents` ever drops it.

## Alternatives considered

- **B — scripted glob install.** Keep the per-package `-e` list but generate it from a script that
  globs every `pyproject.toml`, with a small map for the special extras (providers→openai, svg2pptx→
  none, docling→never). *Rejected:* still hand-maintains the extras map, adds a script to own, and
  gives no lockfile — less idiomatic than the native uv workspace already in use.
- **C — single shared package-list file** referenced by CI + launcher. *Rejected:* still a manual
  list (one instead of two) with no auto-discovery and no lockfile.

A is the idiomatic uv solution, removes the list entirely (globs), and the committed `uv.lock` gives
reproducible installs that also lay groundwork for the later release/publish work.

## Known pre-existing issue surfaced (out of scope)

Running the suite locally **from the worktree** produced one failure:
`test_resolve_deepseek_profile_with_env` asserted the default model `deepseek-chat` but got
`deepseek-v4-pro`. Cause: an app test calls `load_dotenv()` (no path), and python-dotenv **walks up
the directory tree** from the CWD. Because a worktree is nested under the main checkout — which has a
real, gitignored `.env` containing `ASA_DEEPSEEK_MODEL=deepseek-v4-pro` — that value leaks into
`os.environ` and pollutes the later providers test. It passes with the variable cleared, and CI
(no `.env`) is green. This is a **test-isolation weakness predating this change** (a test that loads
the ambient `.env` and mutates global `os.environ`); a proper fix (scope the load, or
monkeypatch-isolate the providers test) is tracked separately and not bundled here.
