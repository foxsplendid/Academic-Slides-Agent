## 1. Converter + tier

- [x] 1.1 Clean-room `latex_to_omml` (common subset, conservative None, no proprietary XSLT)
- [x] 1.2 `AutoFormulaRenderer.to_omml` + `ASA_NATIVE_FORMULA` opt-in (default off)
- [x] 1.3 Compiler native-equation embedding with `mc:AlternateContent` text fallback

## 2. Tests

- [x] 2.1 Converter: well-formed OMML for subset; unsupported → None
- [x] 2.2 OMML round-trips through python-pptx; fallback wrapper present
- [x] 2.3 Unsupported → image fallback; opt-in gating; suite green
