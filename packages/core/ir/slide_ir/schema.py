"""Export Slide-IR to JSON Schema — the type contract consumed by the frontend.

The IR is the single source of truth; frontend TypeScript types are generated from the
schema this module emits.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Deck

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "slide_ir.schema.json"


def export_json_schema() -> dict:
    """Return the JSON Schema for a Deck (which transitively covers SlideIR + all blocks)."""
    return Deck.model_json_schema()


def write_schema(path: Path | None = None) -> Path:
    """Write the JSON Schema to disk and return the path."""
    target = path or DEFAULT_SCHEMA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(export_json_schema(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    written = write_schema()
    print(f"wrote {written}")
