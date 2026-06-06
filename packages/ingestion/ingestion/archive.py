"""Archive ingestion: unpack a .zip and ingest each member by its own type."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from .models import IngestResult


def ingest_zip(
    path: str | Path,
    *,
    workspace: Optional[str | Path] = None,
    cache_dir: Optional[str | Path] = None,
) -> IngestResult:
    from .router import ingest_path  # lazy import to avoid a cycle

    path = Path(path)
    result = IngestResult()
    with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            extracted = Path(archive.extract(name, tmp_dir))
            sub = ingest_path(extracted, workspace=workspace, cache_dir=cache_dir)
            for asset in sub.assets:
                asset.source = f"{path.name}!{name}"  # tag provenance with archive + member
            result.merge(sub)
    return result
