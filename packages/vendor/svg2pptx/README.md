# asa-svg2pptx (vendored, MIT)

SVG → native DrawingML PPTX compiler + deterministic SVG finalize/repair passes.

**Provenance**: vendored from [CRui5in/paper-ppt-agent](https://github.com/CRui5in/paper-ppt-agent)
at commit `6f679fc2ad410597e2e582ceab2a21c72f6bf773` (2026-05-15) — the last revision distributed
under the **MIT license** (the project relicensed to AGPL-3.0 on 2026-05-22; nothing from any
AGPL-era revision is included here). Original copyright (c) 2026 CRui5in — see `LICENSE`.

**Local modifications** (kept minimal, all marked):
- intra-package imports rewritten `backend.generator.*` → `asa_svg2pptx.*`
- `backend.config` replaced by `asa_svg2pptx/_config.py` (canvas formats copied verbatim;
  icons dir now comes from `ASA_SVG_ICONS_DIR`)
- `project_manager.py` vendored alongside (finalize dependency), same import rewrite

Used by Academic-Slides-Agent's premium tier (Path B: VisualCanvas → editable vector shapes).
