## 1. StyleProfile

- [x] 1.1 `pptx_compiler/style.py`: `StyleProfile` dataclass + `ACADEMIC` (current tokens) + a 2nd profile + `get_style(name)`
- [x] 1.2 `compile_deck(*, style=None)` resolves to `ACADEMIC`; threads style to renderers

## 2. Thread tokens

- [x] 2.1 `blocks.py` (`add_rich_text` + render fns) read fonts/sizes/emphasis from `style`
- [x] 2.2 `compiler.py` title sizes + widescreen from `style`; `diagram.py` node colors from `style`

## 3. Wire selection

- [x] 3.1 `build_graph(style=…)` → compile node; `create_app(style=…)`; `build_default_app` reads `ASA_STYLE`

## 4. Tests & verify

- [x] 4.1 Unit: same deck under two profiles → different rendered font names/colors
- [x] 4.2 Unit: default (no style) unchanged; full suite green
