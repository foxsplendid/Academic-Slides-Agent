"""Ingestion result container + shared table-normalization helpers."""

from __future__ import annotations

from typing import Iterable, Optional

from pydantic import BaseModel, Field

from slide_ir import EvidenceAsset, TableBlock


class IngestResult(BaseModel):
    """Output of ingestion: the Evidence Pool (`assets`) + ready `TableBlock`s.

    A table-kind asset references its TableBlock via ``content_ref = "table:<index>"``.
    """

    assets: list[EvidenceAsset] = Field(default_factory=list)
    tables: list[TableBlock] = Field(default_factory=list)

    def merge(self, other: "IngestResult") -> "IngestResult":
        """Fold `other` into this result, re-basing ``table:<index>`` references."""
        offset = len(self.tables)
        for asset in other.assets:
            ref = asset.content_ref
            if isinstance(ref, str) and ref.startswith("table:"):
                try:
                    asset.content_ref = f"table:{int(ref.split(':', 1)[1]) + offset}"
                except ValueError:
                    pass
        self.assets.extend(other.assets)
        self.tables.extend(other.tables)
        return self


def normalize_rows(raw: Iterable[Iterable[object]]) -> list[list[str]]:
    """Stringify cells and drop fully-empty rows."""
    rows = [["" if cell is None else str(cell) for cell in row] for row in raw]
    return [row for row in rows if any(cell.strip() for cell in row)]


def rows_to_table(raw, caption: str, *, needs_human_check: bool = False) -> Optional[TableBlock]:
    """Build a TableBlock from raw rows (first row = header). None if empty."""
    rows = normalize_rows(raw)
    if not rows:
        return None
    header, *data = rows
    ncol = len(header)
    if ncol == 0:
        return None
    columns = [(cell.strip() or f"col{i + 1}") for i, cell in enumerate(header)]
    data = [(row + [""] * (ncol - len(row)))[:ncol] for row in data]
    return TableBlock(columns=columns, rows=data, caption=caption, needs_human_check=needs_human_check)


def add_table(result: IngestResult, table: TableBlock, *, asset_id: str, source: str, locator: dict) -> None:
    """Append a table and a correlated table-kind EvidenceAsset (with provenance)."""
    index = len(result.tables)
    result.tables.append(table)
    result.assets.append(
        EvidenceAsset(
            asset_id=asset_id,
            kind="table",
            content_ref=f"table:{index}",
            source=source,
            locator=locator,
        )
    )
