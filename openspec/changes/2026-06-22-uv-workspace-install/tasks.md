## 1. Workspace root

- [x] 1.1 Add root `pyproject.toml`: virtual project (`[tool.uv] package = false`)
- [x] 1.2 `[tool.uv.workspace]` member globs + exclude (mapper/tables/web)
- [x] 1.3 `[tool.uv.sources]` `{ workspace = true }` for every `asa-*` member
- [x] 1.4 `[dependency-groups] dev` = pytest/jsonschema/httpx + `asa-providers[openai]`

## 2. Member packages

- [x] 2.1 Remove per-package `[tool.uv.sources]` (api, cli, agents, compiler, ingestion, providers)
- [x] 2.2 `apps/api`: declare the directly-imported `asa-pptx-compiler` dependency

## 3. Install / CI / launcher

- [x] 3.1 `ci.yml`: replace the per-package `-e` list with `uv sync --all-packages --locked`
- [x] 3.2 `README.md`: install snippet → `uv sync --all-packages`
- [x] 3.3 `start-dev.bat`: preflight guidance → `uv sync --all-packages`
- [x] 3.4 Generate and commit `uv.lock`

## 4. Verify

- [x] 4.1 `uv lock` resolves (179 packages); `uv sync --all-packages --locked` is clean
- [x] 4.2 License gate OK (88 dists, no GPL/AGPL); svglib/reportlab/docling absent, openai present
- [x] 4.3 Full suite green in a clean env (the lone local failure is a pre-existing `.env`-discovery
      quirk, not a regression — see design.md)
- [x] 4.4 A new package under `packages/`/`apps/` needs no edit to any install list (globs)
