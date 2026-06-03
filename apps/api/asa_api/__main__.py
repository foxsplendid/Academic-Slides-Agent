"""``python -m asa_api`` — serve the default app via uvicorn.

Configuration via env: ``ASA_HOST`` (default 127.0.0.1), ``ASA_PORT`` (8000), ``ASA_OUT_DIR``,
``ASA_LLM_PROVIDER`` + provider keys (``ASA_OPENAI_API_KEY`` / ``ASA_ANTHROPIC_API_KEY`` / ...).
"""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    from .server import build_default_app

    app = build_default_app()
    uvicorn.run(
        app,
        host=os.environ.get("ASA_HOST", "127.0.0.1"),
        port=int(os.environ.get("ASA_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
