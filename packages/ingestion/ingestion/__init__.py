"""ingestion — normalize papers + supplementary data into a provenance-tagged Evidence Pool."""

from .archive import ingest_zip
from .figures import extract_figures
from .mineru import ingest_pdf_mineru, parse_mineru_content_list
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
    "extract_figures",
    "ingest_pdf_mineru",
    "parse_mineru_content_list",
]
