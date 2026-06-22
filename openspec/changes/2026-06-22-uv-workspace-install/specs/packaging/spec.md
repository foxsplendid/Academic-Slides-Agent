## ADDED Requirements

### Requirement: Single-command, drift-free workspace install
The repository SHALL define a uv workspace whose membership is the single source of truth for which
packages exist, so the entire monorepo installs editable with one command (`uv sync --all-packages`)
and a newly added Python package under `packages/` or `apps/` is included without editing any install
list (CI, README, or launcher). Non-distribution directories (empty placeholders; the React
frontend) SHALL be excluded from membership.

#### Scenario: One command installs every package
- **WHEN** `uv sync --all-packages` is run at the repo root
- **THEN** every workspace member is installed editable into the environment, along with the shared
  dev tooling, with no per-package install list

#### Scenario: A new package needs no install-list edit
- **WHEN** a new Python package with a `pyproject.toml` is added under `packages/` or `apps/`
- **THEN** it is discovered by the workspace member globs and installed by `uv sync` with no change
  to `ci.yml`, the README, or `start-dev.bat`

#### Scenario: CI verifies the lockfile is fresh
- **WHEN** CI runs `uv sync --all-packages --locked`
- **THEN** the build fails if `uv.lock` is out of date with the `pyproject.toml` files

### Requirement: License-clean default install
The default workspace install SHALL NOT pull any GPL/AGPL dependency, and SHALL keep LGPL and heavy
optional components behind opt-in extras (SPEC §2). Specifically the `asa-svg2pptx` `raster-fallback`
extra (LGPL svglib) and the `asa-ingestion` `docling` extra MUST NOT be installed by default; the
license gate MUST pass on the default environment.

#### Scenario: Forbidden and heavy extras stay out
- **WHEN** the workspace is installed with `uv sync --all-packages` (no `--all-extras`)
- **THEN** svglib, reportlab, and docling are absent from the environment and `scripts/license_scan.py`
  reports no GPL/AGPL dependency

### Requirement: Packages declare what they import
Each workspace package SHALL declare every sibling package it imports as a dependency, rather than
relying on transitive resolution.

#### Scenario: The API declares the compiler it imports
- **WHEN** `apps/api` imports `pptx_compiler`
- **THEN** `asa-pptx-compiler` appears in `apps/api`'s declared dependencies
