"""ingestion — normalize papers + supplementary data into a provenance-tagged Evidence Pool."""

from .archive import ingest_zip
from .models import IngestResult
from .pdf import ingest_pdf
from .router import ingest, ingest_path
from .spreadsheet import ingest_csv, ingest_xlsx

__all__ = [
    "IngestResult",
    "ingest",
    "ingest_path",
    "ingest_csv",
    "ingest_xlsx",
    "ingest_pdf",
    "ingest_zip",
]
