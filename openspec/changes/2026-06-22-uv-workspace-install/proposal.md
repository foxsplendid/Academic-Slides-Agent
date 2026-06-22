## Why

The monorepo's set of installable packages is enumerated **by hand in more than one place** —
the CI `.github/workflows/ci.yml` install step and the README install snippet — and every package
re-declares its sibling paths in a `[tool.uv.sources]` block. When a package is added, these
hand-maintained lists drift out of sync:

- **2026-06-22:** the new `apps/cli` (`asa-cli`) shipped with tests, but `ci.yml`'s install list
  was not updated, so `pytest` collection failed with `ModuleNotFoundError: No module named
  'asa_cli'` — CI went red (hot-fixed in PR #2).
- Related symptom: `apps/api` imports `asa-pptx-compiler` but never declared it as a dependency
  (it only resolved transitively via `asa-agents`).

The root cause is the absence of a **single source of truth for workspace membership**. This change
introduces a uv workspace so the whole monorepo installs with one command and a new package is
discovered automatically — no install list to keep in sync.

## What Changes

- **New root `pyproject.toml`** — a *virtual* project (`[tool.uv] package = false`, never built or
  published) that declares `[tool.uv.workspace]` members by glob (auto-discovering new packages),
  the inter-package `[tool.uv.sources]` (`workspace = true`, inherited by all members), and a shared
  `dev` dependency-group (pytest / jsonschema / httpx + `asa-providers[openai]`). The empty
  placeholder dirs (`packages/core/mapper`, `…/tables`) and the React `apps/web` are excluded (no
  `pyproject.toml`).
- **Members lose their per-package `[tool.uv.sources]`** — sibling paths now resolve from the
  workspace root, so those blocks were redundant (and a drift surface). Six packages edited.
- **`apps/api` declares `asa-pptx-compiler`** — the previously-undeclared, directly-imported
  dependency.
- **One-command install everywhere** — `ci.yml`, the README, and `start-dev.bat` all use
  `uv sync --all-packages` (CI adds `--locked` to verify the lockfile is fresh). The per-package
  `-e …[extra]` install lists are deleted.
- **Committed `uv.lock`** — reproducible resolution (179 packages).

## Capabilities

### Added Capabilities
- `packaging`: a single-command, drift-free editable install of the whole uv workspace, with a
  license-clean default dependency set.

### Modified Capabilities
- (None — no product behavior changes. `apps/api`'s added dependency declaration merely matches its
  existing imports.)

## Non-goals

- **No version bump / PyPI publish / metadata** (`classifiers`, `project.urls`, `authors`).
  Packages stay at `0.1.0`; publishing is a separate release-readiness change. The committed
  `uv.lock` is groundwork for it but does not undertake it.
- **No `requires-python` unification** — `asa-svg2pptx` stays `>=3.11`, the others `>=3.12`
  (the workspace resolves to `>=3.12`).
- **No new dependency introduced.** uv is already the documented toolchain; the optional extras are
  unchanged. The LGPL `raster-fallback` (svglib/reportlab) and the heavy `docling` extras stay
  opt-in and out of the default install (SPEC §2). No AGPL/GPL is added.
- No change to any package's source code, the Slide-IR contract, the compiler, or the test suite.

## Impact

- New `pyproject.toml` (root) + `uv.lock`; 7 member `pyproject.toml` files edited (6 drop
  `[tool.uv.sources]`; `apps/api` also gains `asa-pptx-compiler`); `ci.yml`, `README.md`,
  `start-dev.bat` switch to `uv sync`. **No source or test changes.**
- Verified locally: `uv sync --all-packages --locked` clean; license gate OK (88 distributions, no
  GPL/AGPL; svglib / reportlab / docling absent, openai present); the full suite passes in a clean
  environment. (One local failure — `test_resolve_deepseek_profile_with_env` — is a pre-existing
  `.env`-discovery test-isolation quirk unrelated to this change; see design.md. CI, which has no
  `.env`, stays green.)
