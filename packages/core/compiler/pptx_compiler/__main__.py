"""CLI: ``python -m pptx_compiler <deck.json> <out.pptx> [template.pptx]``."""

from __future__ import annotations

import sys
from pathlib import Path

from slide_ir import Deck

from .compiler import compile_deck


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2:
        print("usage: python -m pptx_compiler <deck.json> <out.pptx> [template.pptx]", file=sys.stderr)
        return 2
    deck = Deck.model_validate_json(Path(args[0]).read_text(encoding="utf-8"))
    template = args[2] if len(args) > 2 else None
    out = compile_deck(deck, args[1], template=template)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
