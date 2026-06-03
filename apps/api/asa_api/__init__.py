"""asa_api — FastAPI service for Academic-Slides-Agent."""

from .app import create_app
from .server import build_default_app

__all__ = ["create_app", "build_default_app"]
