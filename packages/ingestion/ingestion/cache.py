"""Content-addressed parse cache.

Re-uploading the same paper (e.g. to compare agent modes) shouldn't re-run the expensive parse. A PDF
is keyed by ``sha256(bytes)`` + parser; on a hit we load the cached Evidence Pool. Figure images are
copied into the cache and ``content_ref`` rewritten to the stable cache path, so any run can read them.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Callable

from .models import IngestResult


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def cached_pdf(
    path: str | Path,
    *,
    parser_key: str,
    cache_dir: str | Path,
    parse_fn: Callable[[Path], IngestResult],
) -> IngestResult:
    """Return a cached parse for ``path`` if present, else parse via ``parse_fn`` and cache it."""
    path = Path(path)
    entry = Path(cache_dir) / f"{file_hash(path)}.{parser_key}"
    result_json = entry / "result.json"
    if result_json.is_file():
        try:
            return IngestResult.model_validate_json(result_json.read_text(encoding="utf-8"))
        except Exception:
            pass  # corrupt/old cache -> re-parse below
    result = parse_fn(path)
    _save(entry, result)
    return result


def _save(entry: Path, result: IngestResult) -> None:
    entry.mkdir(parents=True, exist_ok=True)
    fig_dir = entry / "figures"
    for asset in result.assets:
        if asset.kind == "figure" and asset.content_ref and Path(asset.content_ref).is_file():
            fig_dir.mkdir(exist_ok=True)
            dst = fig_dir / Path(asset.content_ref).name
            try:
                shutil.copyfile(asset.content_ref, dst)
                asset.content_ref = str(dst)  # point the cached pool at the persisted copy
            except Exception:
                pass
    try:
        (entry / "result.json").write_text(result.model_dump_json(), encoding="utf-8")
    except Exception:
        pass  # caching is best-effort; never break ingestion
